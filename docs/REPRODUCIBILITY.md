# Reproducibility

Pin `requirements.lock.txt`, build the Python 3.12 Docker image, retain the
Git commit and YAML configuration, and archive each run's metadata and CSV.
Metadata records runtime and cgroup observations. Docker limits do not emulate
the processor or memory behaviour of Danfoss hardware.
