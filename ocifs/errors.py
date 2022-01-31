# coding: utf-8
# Copyright (c) 2021, 2022 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/

import errno
import functools


# Fallback values since some systems might not have these.
EREMOTEIO = getattr(errno, "EREMOTEIO", errno.EIO)


ERROR_CODE_TO_EXCEPTION = {
    "CannotParseRequest": functools.partial(IOError, errno.EINVAL),
    "InvalidParameter": functools.partial(IOError, errno.EINVAL),
    "LimitExceeded": functools.partial(IOError, errno.EINVAL),
    "MissingParameter": functools.partial(IOError, errno.EINVAL),
    "QuotaExceeded": functools.partial(IOError, errno.EINVAL),
    "RelatedResourceNotAuthorizedOrNotFound": functools.partial(IOError, errno.EINVAL),
    "NotAuthenticated": PermissionError,
    "SignUpRequired": PermissionError,
    "NotAuthorized": PermissionError,
    "NotAuthorizedOrNotFound": FileNotFoundError,
    "NotFound": FileNotFoundError,
    "MethodNotAllowed": functools.partial(IOError, errno.EPERM),
    "IncorrectState": functools.partial(IOError, errno.EBUSY),
    "InvalidatedRetryToken": functools.partial(IOError, errno.EBUSY),
    "NotAuthorizedOr ResourceAlreadyExists": functools.partial(IOError, errno.EBUSY),
    "NotAuthorizedOrResourceAlreadyExists": functools.partial(IOError, errno.EBUSY),
    "NoEtagMatch": functools.partial(IOError, errno.EINVAL),
    "TooManyRequests": functools.partial(IOError, errno.EBUSY),
    "InternalServerError": functools.partial(IOError, EREMOTEIO),
    "MethodNotImplemented": functools.partial(IOError, errno.ENOSYS),
    "ServiceUnavailable": functools.partial(IOError, errno.EBUSY),
    "400": functools.partial(IOError, errno.EINVAL),
    "401": PermissionError,
    "402": PermissionError,
    "403": PermissionError,
    "404": FileNotFoundError,
    "405": functools.partial(IOError, errno.EPERM),
    "409": functools.partial(IOError, errno.EBUSY),
    "412": functools.partial(IOError, errno.EINVAL),  # PreconditionFailed
    "429": functools.partial(IOError, errno.EBUSY),  # SlowDown
    "500": functools.partial(IOError, EREMOTEIO),  # InternalError
    "501": functools.partial(IOError, errno.ENOSYS),  # NotImplemented
    "503": functools.partial(IOError, errno.EBUSY),  # SlowDown
}


def translate_oci_error(error, message=None, *args, **kwargs):
    """Convert a ClientError exception into a Python one.
    Parameters
    ----------
    error : oci.exceptions.ServiceError
        The exception returned by the OCI Object Storage API.
    message : str
        An error message to use for the returned exception. If not given, the
        error message returned by the server is used instead.
    *args, **kwargs :
        Additional arguments to pass to the exception constructor, after the
        error message. Useful for passing the filename arguments to ``IOError``.
    Returns
    -------
    An instantiated exception ready to be thrown. If the error code isn't
    recognized, an IOError with the original error message is returned.
    """
    if not hasattr(error, "code") or not hasattr(error, "status"):
        return error
    constructor = ERROR_CODE_TO_EXCEPTION.get(
        error.code, ERROR_CODE_TO_EXCEPTION.get(str(error.status))
    )
    if not constructor:
        # No match found, wrap this in an IOError with the appropriate message.
        return IOError(errno.EIO, message or str(error), *args)

    if not message:
        message = error.message if error.message is not None else str(error)

    return constructor(message, *args, **kwargs)
