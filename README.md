
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
##  OCIFS file system style operations Example for non Data Lake Integration:
```python
from ocifs import OCIFileSystem

fs = OCIFilesystem("~/.oci/config")
# 1.Create empty file or truncate in OCI objectstorage bucket
 fs.touch("oci://<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt", truncate=True, data=b"Welcome to non Data Lake!")
 # 2.Fetch(potentially multiple paths' contents
 fs.cat("oci://<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt")
 # 3.Get metadata about a file from a head or list call
 fs.info("o<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt")
 # 4.Get directory listing page
 fs.ls("<my_bucket>@<my_namespace>/<my_prefix>/", detail=True)
 # 5.Is this entry directory-like?
 fs.isdir("<my_bucket>@<my_namespace>")
 # 6.Is this entry file-like?
 fs.isfile("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt")
 # 7.If there is a file at the given path (including broken links)
 fs.lexists("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt")
 # 8.List of files for the given path
 fs.listdir("<my_bucket>@<my_namespace>/<my_prefix>", detail=True)
 # 9.Get the first ``size`` bytes from file
 fs.head("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt", size=1024)
 # 10.Get the last ``size`` bytes from file
 fs.tail("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt", size=1024)
 # 11.Hash of file properties, to tell if it has changed
 fs.ukey("<my_bucket>@<my_namespace>/<my_prefix>/hello4.txt")
 # 12.Size in bytes of file
 fs.size("<my_bucket>@<my_namespace>/<my_prefix>/hello4.txt")
 # 13.Size in bytes of each file in a list of paths
 paths = ["<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt", "<my_bucket>@<my_namespace>/<my_prefix>/hello3.txt"]
 fs.sizes(paths)
 # 14.Normalise OCI path string into bucket and key.
 fs.split_path("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt")
 # 15.Delete  a file from the  bucket
 fs.rm("<my_bucket>@<my_namespace>/<my_prefix>/hello10.txt")
 # 16.Get the contents of the file as a byte
 fs.read_bytes("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt", start=0, end=13)
 # 17.Get the contents of the file as a string
 fs.read_text("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt", encoding=None, errors=None, newline=None)
 # 18.Get the contents of the file as a byte
 fs.read_block("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt", 0, 13)
 # 19.Open a file for writing/flushing into file in OCI objectstorage bucket
 with fs.open("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt", 'w', autocommit=True) as f:
        f.write("Welcome to Data Lake in Oracle!!!!!!!") # data is flushed and file closed
        f.flush()
 # 20.Open a file for reading a file from OCI objectstorage bucket
 with fs.open("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt") as f:
        print(f.read())
 # 21.Space used by files and optionally directories within a path
 fs.du('<my_bucket>@<my_namespace>/<my_prefix>/lakesharing10.csv')
 # 22.Find files by glob-matching.
 fs.glob("<my_bucket>@<my_namespace>/<my_prefix>/*.txt")
 # 23.Delete multiple files from the same bucket
 pathlist = ["<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt"]
 fs.bulk_delete(pathlist)

```

##  OCIFS file system style operations Example for Data Lake Integration:
```python
from ocifs import OCIFileSystem
fs = OCIFilesystem("~/.oci/config")
# To access the  External Mount bucket got managed by Data lake 
fs.ls("ocilake://<mountname>@lakeocid/<my_prefix>")
# [<my_bucket>@<my_namespace>/<my_prefix>/obj1, <my_bucket>@<my_namespace>/<my_prefix>/obj2]
# To access the  Database Mount bucket got managed by Data lake 
fs.ls("ocilake://<mountname>:database:<databaseKey>@lakeocid/<my_prefix>")
# [<my_bucket>@<my_namespace>/<my_prefix>/obj1, <my_bucket>@<my_namespace>/<my_prefix>/obj2]
# To access the  Table Mount bucket got managed by Data lake 
fs.ls("ocilake://<mountname>:table:<databaseKey>:<tableKey>@lakeocid/<my_prefix>")
# [<my_bucket>@<my_namespace>/<my_prefix>/obj1, <my_bucket>@<my_namespace>/<my_prefix>/obj2]
# To access the  User Mount bucket got managed by Data lake 
fs.ls("ocilake://<mountname>:user:<userOcid>@lakeocid/<my_prefix>")
# [<my_bucket>@<my_namespace>/<my_prefix>/obj1, <my_bucket>@<my_namespace>/<my_prefix>/obj2]

fs.cat("ocilake://<mountname>:database:<databaseKey>@lakeocid/<my_prefix>/obj1")
# b"Hello World"

with fs.open("ocilake://<mountname>:database:<databaseKey>@lakeocid/<my_prefix>/obj3", 'w') as f:
    f.write("Adding a third object.")

with fs.open("ocilake://<mountname>:database:<databaseKey>@lakeocid/<my_prefix>/obj1") as f:
    print(f.read())
# b"Adding a third object."
# 1.Create empty file or truncate in OCI objectstorage bucket
 fs.touch("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt", truncate=True, data=b"Welcome to Data Lake!")
 # 2.Fetch(potentially multiple paths' contents
 fs.cat("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt")
 # 3.Get metadata about a file from a head or list call
 fs.info("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt")
 # 4.Get directory listing page
 fs.ls("ocilake://<mountname>@lakeocid/<my_prefix>/", detail=True)
 # 5.Is this entry directory-like?
 fs.isdir("ocilake://<mountname>@lakeocid")
 # 6.Is this entry file-like?
 fs.isfile("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt")
 # 7.If there is a file at the given path (including broken links)
 fs.lexists("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt")
 # 8.List of files for the given path
 fs.listdir("ocilake://<mountname>@lakeocid/<my_prefix>", detail=True)
 # 9.Get the first ``size`` bytes from file
 fs.head("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt", size=1024)
 # 10.Get the last ``size`` bytes from file
 fs.tail("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt", size=1024)
 # 11.Hash of file properties, to tell if it has changed
 fs.ukey("ocilake://<mountname>@lakeocid/<my_prefix>/hello4.txt")
 # 12.Size in bytes of file
 fs.size("ocilake://<mountname>@lakeocid/<my_prefix>/hello4.txt")
 # 13.Size in bytes of each file in a list of paths
 paths = ["ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt", "ocilake://<mountname>@lakeocid/<my_prefix>/hello3.txt"]
 fs.sizes(paths)
 # 14.Normalise OCI path string into bucket and key.
 fs.split_path("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt")
 # 15.Delete  a file from the  bucket
 fs.touch("<ocilake://<mountname>@lakeocid/<my_prefix>/hello10.txt", truncate=True, data=b"Welcome to Data Lake!")
 fs.rm("ocilake://<mountname>@lakeocid/<my_prefix>/hello10.txt")
 fs.touch("ocilake://<mountname>@lakeocid/<my_prefix>/hello10.txt", truncate=True, data=b"Welcome to Data Lake!")
 # 16.Get the contents of the file as a byte
 fs.read_bytes("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt", start=0, end=13)
 # 17.Get the contents of the file as a string
 fs.read_text("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt", encoding=None, errors=None, newline=None)
 # 18.Get the contents of the file as a byte
 fs.read_block("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt", 0, 13)
 # 19.Open a file for writing/flushing into file in OCI objectstorage bucket
 with fs.open("ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt", 'w', autocommit=True) as f:
        f.write("Welcome to Data Lake in Oracle!!!!!!!") # data is flushed and file closed
        f.flush()
 # 20.Open a file for reading a file from OCI objectstorage bucket
 with fs.open("<my_bucket>@<my_namespace>/<my_prefix>/lakesharing.txt") as f:
        print(f.read())
 # 21.Space used by files and optionally directories within a path
 fs.du('ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing10.csv')
 # 22.Find files by glob-matching.
 fs.glob("ocilake://<mountname>@lakeocid/<my_prefix>/*.txt")
 # 23.Delete multiple files from the same bucket
 pathlist = ["ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing.txt"]
 fs.bulk_delete(pathlist)''
```

### Or Use With Pandas for non Data Lake Integration
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

### Or Use With Pandas for Data Lake Integration
​
```python
import pandas as pd
import ocifs
​
 df = pd.read_csv(
        "ocilake://<mountname>@lakeocid/<my_prefix>/lakesharing10.csv",
        storage_options={"config": "~/.oci/config", "profile": '<profile_name>'
                         }
)
```

### Or Use With PyArrow for non Data Lake Integration
​
```python
import pandas as pd
import ocifs
​
df = pd.read_csv(
    "oci://my_bucket@my_namespace/my_object.csv",storage_options={"config": "~/.oci/config"})
```

### Or Use With PyArrow for Data Lake Integration
​
```python
import ads

import ocifs
import numpy as np
import pyarrow.dataset as pyarrowDs
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd

​
 
 fs = ocifs.OCIFileSystem(config="~/.oci/config", profile='<profile_name>')
 dataset = pyarrowDs.dataset(f"ocilake://<mountname>@lakeocid/userdata1.parquet", filesystem=fs)
 print(dataset.to_table())
 df = pd.DataFrame({'one': [-1, np.nan, 2.5],
                       'two': ['foo', 'bar', 'baz'], 'three': [True, False, True]}, index=list('abc'))
 table = pa.Table.from_pandas(df)
 pq.write_table(table, f"ocilake://<mountname>@lakeocid/example.parquet", filesystem=fs)
 dataset = pyarrowDs.dataset(f"ocilake://<mountname>@lakeocid/example.parquet", filesystem=fs)
    print(dataset.to_table())
```

### Or Use With ADSDataset for non Data Lake Integration
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

### Or Use With ADSDataset for Data Lake Integration
​
```python
import ads
import pandas as pd
from ads.common.auth import default_signer
from ads.dataset.dataset import ADSDataset

​
    ads.set_auth(auth="api_key", oci_config_location="~/.oci/config",  profile="<profile_name>")
    ds = ADSDataset(
        df=pd.read_csv(
            f"ocilake://<mountname>@lakeocid/my_object.csv",
            storage_options=default_signer())
        , type_discovery=False
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
