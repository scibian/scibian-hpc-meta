# scibian-hpc-meta

Meta-packages to install most required packages on Scibian HPC clusters.

## Checks

A check script is provided, it can be run with the following command:

```
$ python3 checks/check-available-pkgs.py [proxy]
```

It notably check all dependencies of the meta-packages are available either in
the Debian ccommunity repositories or the Scibian project repository.
