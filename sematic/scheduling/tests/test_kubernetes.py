# Standard Library
from unittest import mock

import pytest
from kubernetes.client.exceptions import ApiException

# Sematic
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    ResourceRequirements,
)
from sematic.scheduling.kubernetes import (
    JobType,
    KubernetesExternalJob,
    KubernetesJobCondition,
    _schedule_kubernetes_job,
    refresh_job,
    schedule_run_job,
)
from sematic.tests.fixtures import environment_variables  # noqa: F401


@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
@mock.patch("sematic.user_settings.get_all_user_settings")
def test_schedule_kubernetes_job(
    mock_user_settings, k8s_batch_client, mock_kube_config
):
    name = "the-name"
    requests = {"cpu": "42"}
    node_selector = {"foo": "bar"}
    environment_secrets = {"api_key_1": "MY_API_KEY"}
    file_secrets = {"api_key_2": "the_file.txt"}
    secret_root = "/the-secrets"
    image_uri = "the-image"
    namespace = "the-namespace"
    args = ["a", "b", "c"]
    configured_env_vars = {"SOME_ENV_VAR": "some-env-var-value"}

    resource_requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            requests=requests,
            node_selector=node_selector,
            secret_mounts=KubernetesSecretMount(
                environment_secrets=environment_secrets,
                file_secrets=file_secrets,
                file_secret_root_path=secret_root,
            ),
        )
    )
    mock_user_settings.return_value = {"KUBERNETES_NAMESPACE": namespace}
    with environment_variables({"SEMATIC_CONTAINER_IMAGE": image_uri}):
        _schedule_kubernetes_job(
            name=name,
            image=image_uri,
            environment_vars=configured_env_vars,
            namespace=namespace,
            resource_requirements=resource_requirements,
            args=args,
        )

    k8s_batch_client.return_value.create_namespaced_job.assert_called_once()
    _, kwargs = k8s_batch_client.return_value.create_namespaced_job.call_args
    assert kwargs["namespace"] == namespace
    job = kwargs["body"]
    assert job.spec.template.spec.node_selector == node_selector
    secret_volume = job.spec.template.spec.volumes[0]
    assert secret_volume.name == "sematic-func-secrets-volume"
    assert secret_volume.secret.items[0].key == next(iter(file_secrets.keys()))
    assert secret_volume.secret.items[0].path == next(iter(file_secrets.values()))
    container = job.spec.template.spec.containers[0]
    assert container.args == args
    env_vars = container.env
    secret_env_var = next(
        var for var in env_vars if var.name == next(iter(environment_secrets.values()))
    )
    assert secret_env_var.value_from.secret_key_ref.key == next(
        iter(environment_secrets)
    )
    normal_env_var = next(
        var for var in env_vars if var.name == next(iter(configured_env_vars.keys()))
    )
    assert normal_env_var.value == next(iter(configured_env_vars.values()))
    assert container.image == image_uri
    assert container.resources.limits == requests
    assert container.resources.requests == requests


IS_ACTIVE_CASES = [
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=0,
            most_recent_condition=None,
            has_started=False,
            still_exists=True,
        ),
        True,  # job hasn't started yet
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            most_recent_condition=None,
            has_started=True,
            still_exists=True,
        ),
        True,  # job has started and has active pods
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=1,
            most_recent_condition=KubernetesJobCondition.Complete.value,
            has_started=True,
            still_exists=True,
        ),
        False,  # job has completed successfully
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=0,
            most_recent_condition=KubernetesJobCondition.Failed.value,
            has_started=True,
            still_exists=True,
        ),
        False,  # job has failed
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=1,
            most_recent_condition=KubernetesJobCondition.Complete.value,
            has_started=True,
            still_exists=False,
        ),
        False,  # job completed long ago and no longer exists
    ),
    (
        KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                "a", "b", JobType.worker
            ),
            pending_or_running_pod_count=0,
            succeeded_pod_count=0,
            most_recent_condition=None,
            has_started=True,
            still_exists=False,
        ),
        False,  # job was not updated between start and complete dissapearance
    ),
]


@pytest.mark.parametrize(
    "job, expected",
    IS_ACTIVE_CASES,
)
def test_job_is_active(job, expected):
    assert job.is_active() == expected


@mock.patch("sematic.scheduling.kubernetes.load_kube_config")
@mock.patch("sematic.scheduling.kubernetes.kubernetes.client.BatchV1Api")
def test_refresh_job(mock_batch_api, mock_load_kube_config):
    mock_k8s_job = mock.MagicMock()
    mock_batch_api.return_value.read_namespaced_job_status.return_value = mock_k8s_job
    run_id = "the-run-id"
    namespace = "the-namespace"
    job = KubernetesExternalJob(
        kind="k8s",
        try_number=0,
        external_job_id=KubernetesExternalJob.make_external_job_id(
            run_id, namespace, JobType.worker
        ),
        pending_or_running_pod_count=0,
        succeeded_pod_count=1,
        most_recent_condition=None,
        has_started=True,
        still_exists=True,
    )
    mock_k8s_job.status.active = 1

    # should be impossible (or at least highly unlikely) to have 1 active and
    # 1 succeeded, but perhaps it could happen if 1 pod was terminating due
    # to an eviction and another had already started and completed. Just testing
    # here that the data is pulled from the job properly
    mock_k8s_job.status.succeeded = 1

    success_condition = mock.MagicMock()
    success_condition.status = "True"
    success_condition.type = KubernetesJobCondition.Complete.value
    success_condition.lastTransitionTime = 1

    fail_condition = mock.MagicMock()
    # aka, the Failed condition does NOT apply. K8s doesn't really set
    # conditions like this AFAICT, but this is what the semantics of
    # the conditions is supposed to be.
    fail_condition.status = "False"
    fail_condition.type = KubernetesJobCondition.Failed.value
    fail_condition.lastTransitionTime = 2
    mock_k8s_job.status.conditions = [
        success_condition,
        fail_condition,
    ]
    job = refresh_job(job)

    assert job.has_started
    assert job.pending_or_running_pod_count == 1
    assert job.most_recent_condition == KubernetesJobCondition.Complete.value
    assert job.still_exists

    mock_batch_api.return_value.read_namespaced_job_status.side_effect = ApiException()
    mock_batch_api.return_value.read_namespaced_job_status.side_effect.status = 404
    job = refresh_job(job)
    assert not job.still_exists


@mock.patch("sematic.user_settings.get_all_user_settings")
@mock.patch("sematic.scheduling.kubernetes._schedule_kubernetes_job")
def test_schedule_run_job(mock_schedule_k8s_job, mock_user_settings):
    settings = {"SOME_SETTING": "SOME_VALUE"}
    resource_requests = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(),
    )
    image = "the_image"
    run_id = "run_id"
    namespace = "the-namespace"
    mock_user_settings.return_value = {"KUBERNETES_NAMESPACE": namespace}
    schedule_run_job(
        run_id=run_id,
        image=image,
        user_settings=settings,
        resource_requirements=resource_requests,
        try_number=1,
    )
    mock_schedule_k8s_job.assert_called_with(
        name=f"sematic-worker-{run_id}",
        image=image,
        environment_vars=settings,
        namespace=namespace,
        resource_requirements=resource_requests,
        args=["--run_id", run_id],
    )
