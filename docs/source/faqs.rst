Frequently Asked Questions
---------------------------


**Is ocifs asynchronous?**

No. Ocifs currently inherits the AbstractFile and AbstractFileSystem classes, rather than the Async versions of these. This development may happen in the future if there's enough interest.


**Does ocifs use multipart uploads?**

Yes. Ocifs uses multipart uploads to upload files to Object Storage when the file is larger than 5 GB.


**Can I bring my own signer?**

Yes. Whether you want to use Resource Principal, Instance Principal, or some other type of OCI signer, simply pass that signer to the OCIFileSystem init method.


**Can I use ocifs with a different region?**

Yes, pass this region into the OCIFileSystem init method, and ensure your auth credentials work cross-region.


**Can I use ocifs with a different tenancy?**

Yes, pass this tenancy into the OCIFileSystem init method, and ensure your auth credentials work cross-region.


**Can I set auth once and forget?**

Yes, you can use environment variables: `OCIFS_IAM_TYPE`, `OCIFS_CONFIG_LOCATION`, `OCIFS_CONFIG_PROFILE`. Read more in the Getting Connected section.
