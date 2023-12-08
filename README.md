
# Oracle Cloud Infrastructure Object Storage fsspec Implementation


[![PyPI](https://img.shields.io/pypi/v/ocifs.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ocifs/) [![Python](https://img.shields.io/pypi/pyversions/ocifs.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ocifs/)


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
##  OCIFS file system style operations Example:
```python
from ocifs import OCIFileSystem

fs = OCIFilesystem("~/.oci/config")
# 1.Create empty file or truncate in OCI objectstorage bucket
 fs.touch("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt", truncate=True, data=b"Writing to Object Storage!")
 # 2.Fetch(potentially multiple paths' contents
 fs.cat("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt")
 # 3.Get metadata about a file from a head or list call
 fs.info("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt")
 # 4.Get directory listing page
 fs.ls("oci://<my_bucket>@<my_namespace>/<my_prefix>/", detail=True)
 # 5.Is this entry directory-like?
 fs.isdir("oci://<my_bucket>@<my_namespace>")
 # 6.Is this entry file-like?
 fs.isfile("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt")
 # 7.If there is a file at the given path (including broken links)
 fs.lexists("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt")
 # 8.List of files for the given path
 fs.listdir("oci://<my_bucket>@<my_namespace>/<my_prefix>", detail=True)
 # 9.Get the first ``size`` bytes from file
 fs.head("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt", size=1024)
 # 10.Get the last ``size`` bytes from file
 fs.tail("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt", size=1024)
 # 11.Hash of file properties, to tell if it has changed
 fs.ukey("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt")
 # 12.Size in bytes of file
 fs.size("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt")
 # 13.Size in bytes of each file in a list of paths
 paths = ["oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt"]
 fs.sizes(paths)
 # 14.Normalise OCI path string into bucket and key.
 fs.split_path("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt")
 # 15.Delete  a file from the  bucket
 fs.rm("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt")
 # 16.Get the contents of the file as a byte
 fs.read_bytes("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt", start=0, end=13)
 # 17.Get the contents of the file as a string
 fs.read_text("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt", encoding=None, errors=None, newline=None)
 # 18.Get the contents of the file as a byte
 fs.read_block("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt", 0, 13)
 # 19.Open a file for writing/flushing into file in OCI objectstorage bucket
 # content_type is guessed from filename, can be passed explicitly for unkonwn mimetype while writing file
 with fs.open("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt", 'w', autocommit=True, content_type=None) as f:
        f.write("Writing data to buffer, before manually flushing and closing.") # data is flushed and file closed
        f.flush()
 # 20.Open a file for reading a file from OCI objectstorage bucket
 with fs.open("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt") as f:
        print(f.read())
 # 21.Space used by files and optionally directories within a path
 fs.du("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello10.csv")
 # 22.Find files by glob-matching.
 fs.glob("oci://<my_bucket>@<my_namespace>/<my_prefix>/*.txt")
 # 23.Renames an object in a particular bucket in tenancy namespace on OCI
 fs.rename("oci://<my_bucket>@<my_namespace>/<my_prefix>/hello.txt", "oci://<my_bucket>@<my_namespace>/<my_prefix>/hello2.txt")
 # 24.Delete multiple files from the same bucket
 pathlist = ["oci://<my_bucket>@<my_namespace>/<my_prefix>/hello2.txt"]
 fs.bulk_delete(pathlist)

```



### Or Use With Pandas
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

### Or Use With PyArrow
​
```python
import pandas as pd
import ocifs
​
df = pd.read_csv(
    "oci://my_bucket@my_namespace/my_object.csv",storage_options={"config": "~/.oci/config"})
```

### Or Use With ADSDataset
​
```python
import ads
import pandas as pd
from ads.common.auth import default_signer
from ads.dataset.dataset import ADSDataset

​
    ads.set_auth(auth="api_key", oci_config_location="~/.oci/config", profile="<profile_name>")
    ds = ADSDataset(
        df=pd.read_csv(f"oci://my_bucket@my_namespace/my_object.csv", storage_options=default_signer()),
        type_discovery=False
    )
    print(ds.df)
```

​
## Getting Started
```bash
python3 -m pip install ocifs
```

## Software Prerequisites
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

## Environment Variables for enabling Logging:
To quickly see all messages, you can set the environment variable OCIFS_LOGGING_LEVEL=DEBUG.
```bash
export OCIFS_LOGGING_LEVEL=DEBUG
```

## Documentation
* [![PyPI](https://img.shields.io/pypi/v/ocifs.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ocifs/) [![Python](https://img.shields.io/pypi/pyversions/ocifs.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ocifs/)
* [ocifs Documentation](https://ocifs.readthedocs.io/en/latest/index.html)
* [ocifs GitHub](https://github.com/oracle/ocifs)

## Support
[The built-in filesystems in `fsspec`](https://filesystem-spec.readthedocs.io/en/latest/api.html#built-in-implementations) are maintained by the `intake` project team, where as `ocifs` is an external implementation (similar to `s3fs`, `gcsfs`, `adl/abfs`, and so on), which is maintained by Oracle.

## Contributing
This project welcomes contributions from the community. Before submitting a pull request, please [review our contribution guide](./CONTRIBUTING.md)

## Security
Please consult the [security guide](./SECURITY.md) for our responsible security vulnerability disclosure process

## License
Copyright (c) 2021, 2023 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
