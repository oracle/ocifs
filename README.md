
## Oracle Cloud Infrastructure Object Storage fsspec implementation
​
​
The [Oracle Cloud Infrastructure Object Storage](https://docs.oracle.com/en-us/iaas/Content/Object/Concepts/objectstorageoverview.htm) service is an internet-scale, high-performance storage platform that offers reliable and cost-efficient data durability. With Object Storage, you can safely and securely store or retrieve data directly from the internet or from within the cloud platform.
​
`ocifs` is part of the `fsspec` [intake/filesystem_spec ecosystem](https://github.com/intake/filesystem_spec)
​
> a template or specification for a file-system interface, that specific implementations should follow, so that applications making use of them can rely on a common interface and not have to worry about the specific internal implementation decisions with any given backend.
​
`ocifs` joins the list of file systems supported with this package.
​
The `intake/filesystem_spec` project is used by [Pandas](https://pandas.pydata.org/), [Dask](https://dask.org/) and other data libraries in python, this package adds Oracle OCI Object Storage capabilties to these libraries.
​
## Example Usage:
​
```python
import pandas as pd
import ocifs
​
df = pd.read_csv(
    "oci://my_bucket@my_namespace/myobject.csv",
    storage_options={"config": "~/.oci/config"},
)
```
​
## Getting Started:
```bash
python3 -m pip install ocifs
```

## Software Prerequisites:
Python >= 3.6

## Documentation:
[ocifs Documentation](https://docs.oracle.com/en-us/iaas/tools/ocifs-sdk/latest/index.html)

## Support
​
[The built-in filesystems in `fsspec`](https://filesystem-spec.readthedocs.io/en/latest/api.html#built-in-implementations) are maintained by the `intake` project team, where as `ocifs` is an external implementation (similar to `s3fs`, `gcsfs`, `adl/abfs`, and so on), which is maintained by Oracle.
