#   Copyright 2014-2020 CERN
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import warnings
from datetime import timedelta

from fts3.rest.client import Submitter
from fts3.rest.client import ClientError
from .delegate import delegate

# Remove line when "spacetoken" field is removed
warnings.filterwarnings(action="always", category=DeprecationWarning, module="fts3")


class JobIdGenerator:
    standard = "standard"  # Default algorithm using uuid1
    deterministic = "deterministic"  # Deterministic algorithm using uuid5 with base_id+vo+sid given by the user


def cancel(context, job_id, file_ids=None):
    """
    Cancels a job

    Args:
        context: fts3.rest.client.context.Context instance
        job_id:  The job to cancel

    Returns:
        The terminal state in which the job has been left.
        Note that it may not be CANCELED if the job finished already!
    """
    submitter = Submitter(context)
    return submitter.cancel(job_id, file_ids)


def cancel_all(context, vo_name=None):
    """
    Cancel all jobs within a given VO or FTS3 (needs enough privileges)

    Args:
        context: fts3.rest.client.context.Context instance
        vo_name: The VO name, or None to cancel all jobs

    Returns:
        None
    """
    submitter = Submitter(context)
    return submitter.cancel_all(vo_name)


def new_transfer(
    source,
    destination,
    checksum="ADLER32",
    filesize=None,
    activity=None,
    scitag=None,
    metadata=None,
    staging_metadata=None,
    archive_metadata=None,
    selection_strategy="auto",
    **kwargs,
):
    """
    Creates a new transfer pair

    Args:
        source:             Source SURL
        destination:        Destination SURL
        checksum:           Checksum
        filesize:           File size
        activity:           Transfer activity label
        scitag:             SciTag flow label
        metadata:           Metadata to bind to the transfer
        staging_metadata:   Staging Metadata to bind to the bringonline operation
        archive_metadata:   Archive Metadata to bind to the archiving operation
        selection_strategy: Selection strategy to implement for multiple replica Jobs

    Returns:
        An initialized transfer
    """
    transfer = dict(
        sources=[source],
        destinations=[destination],
    )
    if checksum:
        transfer["checksum"] = checksum
    if filesize:
        transfer["filesize"] = filesize
    if activity:
        transfer["activity"] = activity
    if scitag:
        if not (65 <= scitag <= 65535):
            raise ClientError(
                "Invalid SciTag value: {} (not in [65, 65535] range)".format(scitag)
            )
        transfer["scitag"] = scitag
    if metadata:
        transfer["metadata"] = metadata
    if staging_metadata:
        transfer["staging_metadata"] = staging_metadata
    if archive_metadata:
        transfer["archive_metadata"] = archive_metadata
    if selection_strategy:
        transfer["selection_strategy"] = selection_strategy

    source_token = kwargs["source_token"] if "source_token" in kwargs else None
    destination_token = (
        kwargs["destination_token"] if "destination_token" in kwargs else None
    )

    if source_token or destination_token:
        if not (source_token and destination_token):
            raise ClientError("Both source and destination tokens should be given")
        transfer["source_tokens"] = [source_token]
        transfer["destination_tokens"] = [destination_token]

    return transfer


def add_alternative_source(transfer, alt_source):
    """
    Adds an alternative source to a transfer

    Args:
        transfer:   A dictionary created with new_transfer
        alt_source: Alternative source

    Returns:
        For convenience, transfer
    """
    transfer["sources"].push_back(alt_source)
    return transfer


def new_job(
    transfers=None,
    deletion=None,
    verify_checksum=False,
    reuse=None,
    overwrite=False,
    overwrite_on_retry=False,
    overwrite_when_only_on_disk=False,
    overwrite_hop=False,
    multihop=False,
    source_spacetoken=None,
    destination_spacetoken=None,
    bring_online=None,
    dst_file_report=False,
    archive_timeout=None,
    copy_pin_lifetime=None,
    retry=-1,
    retry_delay=0,
    priority=None,
    metadata=None,
    strict_copy=False,
    disable_cleanup=False,
    max_time_in_queue=None,
    timeout=None,
    id_generator=JobIdGenerator.standard,
    sid=None,
    s3alternate=False,
    nostreams=1,
    buffer_size=None,
    unmanaged_tokens=False,
    **kwargs,
):
    """
    Creates a new dictionary representing a job

    Args:
        transfers:                   Initial list of transfers
        deletion:                    Delete files
        verify_checksum:             Enable checksum verification: source, destination, both or none
        reuse:                       Enable reuse (all transfers are handled by the same process)
        overwrite:                   Overwrite the destinations if exist
        overwrite_on_retry:          Enable overwrite files only during FTS retries
        overwrite_when_only_on_disk: Overwrite file when file locality is only disk
        overwrite_hop:               Overwrite all files expect final destination in a multihop job
        multihop:                    Treat the transfer as a multihop transfer
        source_spacetoken:           Source space token
        destination_spacetoken:      Destination space token
        bring_online:                Bring online timeout
        dst_file_report:             Report on the destination tape file if it already exists and overwrite is off
        archive_timeout:             Archive timeout
        copy_pin_lifetime:           Pin lifetime
        retry:                       Number of retries: <0 is no retries, 0 is server default, >0 is whatever value is passed
        retry_delay:                 Minutes to wait before next retry
        priority:                    Job priority
        metadata:                    Metadata to bind to the job
        strict_copy:                 Execute only the TPC part of a transfer (no other preparation)
        disable_cleanup:             Do not perform the destination file clean-up on transfer failure
        max_time_in_queue:           Maximum number
        timeout:                     Transfer timeout
        id_generator:                Job id generator algorithm
        sid:                         Specific id given by the client
        s3alternate:                 Use S3 alternate URL schema
        nostreams:                   Number of streams
        buffer_size:                 TCP buffer size (in bytes) that will be used for the given transfer-job
        unmanaged_tokens:            Instruct server to not manage the token lifecycle

    Returns:
        An initialized dictionary representing a job
    """
    if transfers is None and deletion is None:
        raise ClientError("Bad request: No transfers or deletion jobs are provided")
    if transfers is None:
        transfers = []

    if isinstance(verify_checksum, str):
        if verify_checksum not in ("source", "target", "both", "none"):
            raise ClientError(
                "Bad request: verify_checksum does not contain a valid value"
            )

    overwrite_flags_count = sum(
        [overwrite, overwrite_on_retry, overwrite_when_only_on_disk, overwrite_hop]
    )
    # "overwrite_hop" and "overwrite_when_only_on_disk" allowed to work together
    if overwrite_flags_count > 1 and not (
        overwrite_flags_count == 2 and overwrite_hop and overwrite_when_only_on_disk
    ):
        raise ClientError(
            "Bad request: Incompatible overwrite flags used at the same time"
        )
    if overwrite_when_only_on_disk and (
        archive_timeout is None or archive_timeout <= 0
    ):
        raise ClientError(
            "Bad request: 'overwrite_when_only_on_disk' requires 'archive_timeout' to be set"
        )

    # Deprecate the "spacetoken" field (will be removed in FTS v3.14)
    if "spacetoken" in kwargs:
        warnings.warn(
            "Variable 'spacetoken' is deprecated and will be removed in FTS v3.14. Please use 'destination_spacetoken' instead!",
            DeprecationWarning,
        )
        if kwargs["spacetoken"] and not destination_spacetoken:
            destination_spacetoken = kwargs["spacetoken"]

    params = dict(
        verify_checksum=verify_checksum,
        reuse=reuse,
        destination_spacetoken=destination_spacetoken,
        bring_online=bring_online,
        dst_file_report=dst_file_report,
        archive_timeout=archive_timeout,
        copy_pin_lifetime=copy_pin_lifetime,
        job_metadata=metadata,
        source_spacetoken=source_spacetoken,
        overwrite=overwrite,
        overwrite_on_retry=overwrite_on_retry,
        overwrite_when_only_on_disk=overwrite_when_only_on_disk,
        overwrite_hop=overwrite_hop,
        multihop=multihop,
        retry=retry,
        retry_delay=retry_delay,
        priority=priority,
        strict_copy=strict_copy,
        disable_cleanup=disable_cleanup,
        max_time_in_queue=max_time_in_queue,
        timeout=timeout,
        id_generator=id_generator,
        sid=sid,
        s3alternate=s3alternate,
        nostreams=nostreams,
        buffer_size=buffer_size,
        unmanaged_tokens=unmanaged_tokens,
    )
    job = dict(files=transfers, delete=deletion, params=params)
    return job


def new_staging_job(
    files,
    bring_online=None,
    copy_pin_lifetime=None,
    source_spacetoken=None,
    destination_spacetoken=None,
    metadata=None,
    priority=None,
    id_generator=JobIdGenerator.standard,
    sid=None,
    **kwargs,
):
    """
        Creates a new dictionary representing a staging job

    Args:
        files:                  Array of surls to stage. Each item can be either a string or a dictionary with keys surl and metadata
        bring_online:           Bring online timeout
        copy_pin_lifetime:      Pin lifetime
        source_spacetoken:      Source space token
        destination_spacetoken: Destination spacetoken
        metadata:               Metadata to bind to the job
        priority:               Job priority
        id_generator:           Job id generator algorithm
        sid:                    Specific id given by the client

    Returns:
        An initialized dictionary representing a staging job
    """
    if (bring_online is None or bring_online <= 0) and (
        copy_pin_lifetime is None or copy_pin_lifetime <= 0
    ):
        raise ClientError(
            "Bad request: both 'bring_online' and 'copy_pin_lifetime' are not positive numbers"
        )

    transfers = []
    for trans in files:
        if isinstance(trans, dict):
            surl = trans["surl"]
            meta = trans["metadata"]
            staging_meta = trans["staging_metadata"]
        elif isinstance(trans, str):
            surl = trans
            meta = staging_meta = None
        else:
            raise AttributeError("Unexpected input type %s" % type(files))

        transfers.append(
            new_transfer(
                source=surl,
                destination=surl,
                metadata=meta,
                staging_metadata=staging_meta,
            )
        )

    # Deprecate the "spacetoken" field (will be removed in FTS v3.14)
    if "spacetoken" in kwargs:
        warnings.warn(
            "Variable 'spacetoken' is deprecated and will be removed in FTS v3.14. Please use 'destination_spacetoken' instead!",
            DeprecationWarning,
        )
        if kwargs["spacetoken"] and not destination_spacetoken:
            destination_spacetoken = kwargs["spacetoken"]

    params = dict(
        source_spacetoken=source_spacetoken,
        destination_spacetoken=destination_spacetoken,
        bring_online=bring_online,
        copy_pin_lifetime=copy_pin_lifetime,
        job_metadata=metadata,
        priority=priority,
        id_generator=id_generator,
        sid=sid,
    )
    job = dict(files=transfers, params=params)
    return job


def new_delete_job(
    files,
    spacetoken=None,
    metadata=None,
    priority=None,
    id_generator=JobIdGenerator.standard,
    sid=None,
):
    """
    Creates a new dictionary representing a deletion job

    Args:
        files:        Array of surls to delete. Each item can be either a string or a dictionary with keys surl and metadata
        spacetoken:   Deletion spacetoken
        metadata:     Metadata to bind to the job
        priority:     Job priority
        id_generator: Job id generator algorithm
        sid:          Specific id given by the client

    Return
        An initialized dictionary representing a deletion job
    """
    params = dict(
        source_spacetoken=spacetoken,
        job_metadata=metadata,
        priority=priority,
        id_generator=id_generator,
        sid=sid,
    )
    job = dict(delete=files, params=params)
    return job


def submit(
    context,
    job,
    delegation_lifetime=timedelta(hours=7),
    force_delegation=False,
    delegate_when_lifetime_lt=timedelta(hours=2),
):
    """
    Submits a job

    Args:
        context: fts3.rest.client.context.Context instance
        job:     Dictionary representing the job
        delegation_lifetime: Delegation lifetime
        force_delegation:    Force delegation even if there is a valid proxy
        delegate_when_lifetime_lt: If the remaining lifetime on the delegated proxy is less than this interval,
                  do a new delegation

    Returns:
        The job id
    """
    delegate(context, delegation_lifetime, force_delegation, delegate_when_lifetime_lt)
    submitter = Submitter(context)
    params = job.get("params", {})
    return submitter.submit(
        transfers=job.get("files", None),
        delete=job.get("delete", None),
        staging=job.get("staging", None),
        **params,
    )
