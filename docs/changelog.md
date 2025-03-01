<!--
When updating the version, update versions.py and wheel_version.bzl accordingly.
Lines for version numbers should always be formatted as `* MAJOR.MINOR.PATCH`
with nothing else on the line.
-->
* HEAD
* 0.14.0
    * [feature] BREAKING CHANGE: For cloud execution, users submitting pipelines no
      longer need Kubernetes access. Users who have deployed the Sematic server using
      docker will need to either (a) switch to deploying the server on Kubernetes or
      (b) use their Sematic deployment only for metadata tracking instead of metadata
      tracking + cloud execution.
    * [bugfix] Remove job environment variables from resolution API response
    * [improvement] Lower the probability of evictions of resolution jobs and improve
      handling of that situation
* 0.13.0
    * [bugfix] Bugfix for dicitonary visualization
    * [feature] When running in cloud mode, have the server log to stdout
    * [feature] Enable mounting Kubernetes secrets into the container
* 0.12.0
    * [feature] BREAKING CHANGE: Allow specifying resource requirements for Kubernetes
    jobs. `KubernetesResourceRequirements` has a new required field, `requests`
    * [feature] Add `has_container_image()` API for better control over launch workflows
    * [bugfix] Pass API key to request to fetch root run
* 0.11.0
    * [feature] Add a `get_artifact_value` API to retreive artifacts by ID
    * [feature] Add ability to link to individual runs on the UI, not just pipelines
    * [feature] Add option to serve local server from 0.0.0.0
    * [feature] Add capability to use different API URLs for local vs remote client usage
    * [feature] Enable environment variable to change Sematic config directory
    * [improvement] Add exceptions and other improved app logs to the server log files
    * [bugfix] Solve a bug with displaying empty lists in the UI
* 0.10.0
    * [improvement] Add support for python 3.8
    * [improvement] Friendly error message for unsupported Python version
    * [improvement] Friendly error message when clients don't match server version
* 0.9.0
    * [feature] Grafana integration for log panels
* 0.8.0
    * [feature] Capture exception stack traces and display in UI
* 0.7.0
    * [feature] Optional authentication with Google OAuth
* 0.6.0
    * [feature] Cloud execution with `CloudResolver`
    * [feature] Dependency packaging with the `sematic_pipeline` Bazel wheel
* 0.5.1
    * [bugfix] Fix JSON summary of Pandas dataframes with timestamp fields
* 0.5.0
    * [feature] `getitem` support for futures of list, tuples, dictionaries
    * [feature] `__iter__` support for futures of tuples
* 0.4.0
    * [feature] ability to deploy the Sematic API to a cloud instance and run
      pipelines against it (pipeline still runs locally)
    * [improvement] Rename `$ sematic credentials` to `$ sematic settings` to be
      able to store other things than credentials.
* 0.3.0
    * [feature] Support for Tuple types
    * [feature] Support for Dict types
    * [feature] `SnowflakeTable` type
    * [feature] `$ sematic credentials set <app> <var> <value>` CLI command
* 0.2.0
    * [bugfix] UI scroll issues
    * [bugfix] Dataframe UI previews fails for null/NaN values
    * [improvement] link to docs in exceptions for unsupported future operations
    * [example] dynamic graph examples
* 0.1.2-alpha
    * [bugfix] Fix example execution
* 0.1.1-alpha
    * [feature] Support for returning and passing lists of futures
    * [example] Dummy dynamic graph
    * [bugfix] List UI display
    * [improvement] Streamline examples, improve CLI experience
* 0.1.0-alpha
    * [feature] Show run panel when clicking run in DAG
    * [feature] When switching root run, stay on same function if possible
    * [feature] Discord link in side bar
    * [feature] Notes
    * [feature] `$ sematic new` CLI command
    * [bugfix] Style improvements to DAV view
* 0.0.4-alpha
    * New full-page app UI layout
* 0.0.3-alpha.2
    * [bugfix] Fix date display to cnvert from UTC
    * [bugfix] Fix migration bootstrapping to guarantee order of migrations
    * [feature] UI support for `pandas.DataFrame`
    * [feature] UI support for `matplotlib.figure.Figure`
    * [example] New liver cirrhosis prediction model (SKLearn, XGBoost)
* 0.0.2.alpha.1654828599
    * Initial release