
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
```python
from ocifs import OCIFileSystem

fs = OCIFilesystem("~/.oci/config")
fs.ls("oci://<my_bucket>@<my_namespace>/<my_prefix>")
# [<my_bucket>@<my_namespace>/<my_prefix>/obj1, <my_bucket>@<my_namespace>/<my_prefix>/obj2]

fs.cat("oci://<my_bucket>@<my_namespace>/<my_prefix>/obj1")
# b"Hello World"

with fs.open("oci://<my_bucket>@<my_namespace>/<my_prefix>/obj3", 'w') as f:
    f.write("Adding a third object.")

fs.copy("oci://<my_bucket>@<my_namespace>/<my_prefix>/obj3", "oci://<my_bucket>@<my_namespace>/<my_prefix>/obj1")

with fs.open("oci://<my_bucket>@<my_namespace>/<my_prefix>/obj1") as f:
    print(f.read())
# b"Adding a third object."
```

### Or Use With Pandas:
​
```python
import pandas as pd
import ocifs
​
df = pd.read_csv(
    "oci://my_bucket@my_namespace/my_object.csv",
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

## Environment Variables for Authentication:
```bash
export OCIFS_IAM_TYPE=api_key
export OCIFS_CONFIG_LOCATION=~/.oci/config
export OCIFS_CONFIG_PROFILE=DEFAULT
```

Note, if you are operating on OCI with an alternative valid signer, such as resource principal, instead set the following:
```bash
export OCIFS_IAM_TYPE=resource_principal
```

## Documentation:
* [![PyPI](https://img.shields.io/pypi/v/ocifs.svg)](https://pypi.org/project/ocifs/)
* [ocifs Documentation](https://ocifs.readthedocs.io/en/latest/index.html)
* [ocifs GitHub](https://github.com/oracle/ocifs)

## Support
​
[The built-in filesystems in `fsspec`](https://filesystem-spec.readthedocs.io/en/latest/api.html#built-in-implementations) are maintained by the `intake` project team, where as `ocifs` is an external implementation (similar to `s3fs`, `gcsfs`, `adl/abfs`, and so on), which is maintained by Oracle.
