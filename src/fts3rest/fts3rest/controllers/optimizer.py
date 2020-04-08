#   Copyright  Members of the EMI Collaboration, 2013.
#   Copyright 2020 CERN
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
"""
Optimizer logging tables
"""

from werkzeug.exceptions import BadRequest


import json
import logging
from flask import request, current_app as app
from fts3rest.model.meta import Session
from fts3rest.lib.helpers.misc import get_input_as_dict
from fts3.model import OptimizerEvolution, Optimizer
from datetime import datetime
from fts3rest.lib.http_exceptions import *
from fts3rest.lib.helpers.jsonify import jsonify


@jsonify
def is_enabled():
    """
    Indicates if the optimizer is enabled in the server
    """
    return app.config["fts3.Optimizer"]


@jsonify
def evolution():
    """
    Returns the optimizer evolution
    """
    evolution = Session.query(OptimizerEvolution)
    if "source_se" in request.values and request.values["source_se"]:
        evolution = evolution.filter(
            OptimizerEvolution.source_se == request.values["source_se"]
        )
    if "dest_se" in request.values and request.values["dest_se"]:
        evolution = evolution.filter(
            OptimizerEvolution.dest_se == request.values["dest_se"]
        )

    evolution = evolution.order_by(OptimizerEvolution.datetime.desc())

    return evolution[:50]


@jsonify
def get_optimizer_values():
    """
    Returns the current number of actives and streams
    """
    optimizer = Session.query(Optimizer)
    if "source_se" in request.values and request.values["source_se"]:
        optimizer = optimizer.filter(Optimizer.source_se == request.values["source_se"])
    if "dest_se" in request.values and request.values["dest_se"]:
        optimizer = optimizer.filter(Optimizer.dest_se == request.values["dest_se"])

    optimizer = optimizer.order_by(Optimizer.datetime.desc())

    return optimizer


@jsonify
def set_optimizer_values():
    """
    Set the number of actives and streams
    """
    input_dict = get_input_as_dict(request)
    source_se = input_dict.get("source_se", None)
    dest_se = input_dict.get("dest_se", None)
    rationale = input_dict.get("rationale", None)

    current_time = datetime.utcnow()
    if not source_se or not dest_se:
        raise BadRequest("Missing source and/or destination")

    try:
        active = int(input_dict.get("active", 2))
    except Exception as e:
        raise BadRequest("Active must be an integer (%s)" % str(e))
    if active < 0:
        raise BadRequest("Active must be positive (%s)" % str(active))

    try:
        nostreams = int(input_dict.get("nostreams", 1))
    except Exception as e:
        raise BadRequest("Nostreams must be an integer (%s)" % str(e))
    if nostreams < 0:
        raise BadRequest("Nostreams must be positive (%s)" % str(nostreams))

    try:
        diff = int(input_dict.get("diff", 1))
    except Exception as e:
        raise BadRequest("Diff must be an integer (%s)" % str(e))
    if diff < 0:
        raise BadRequest("Diff must be positive (%s)" % str(diff))
    try:
        actual_active = int(input_dict.get("actual_active", 1))
    except Exception as e:
        raise BadRequest("Actual_active must be an integer (%s)" % str(e))
    if actual_active < 0:
        raise BadRequest("Actual_active must be positive (%s)" % str(actual_active))
    try:
        queue_size = int(input_dict.get("queue_size", 1))
    except Exception as e:
        raise BadRequest("Queue_size must be an integer (%s)" % str(e))
    if queue_size < 0:
        raise BadRequest("Queue_size must be positive (%s)" % str(queue_size))
    try:
        ema = float(input_dict.get("ema", 0))
    except Exception as e:
        raise BadRequest("Ema must be a float (%s)" % str(e))
    if ema < 0:
        raise BadRequest("Ema must be positive (%s)" % str(ema))
    try:
        throughput = float(input_dict.get("throughput", 0))
    except Exception as e:
        raise BadRequest("Throughput must be a float (%s)" % str(e))
    if throughput < 0:
        raise BadRequest("Throughput must be positive (%s)" % str(throughput))
    try:
        success = float(input_dict.get("success", 0))
    except Exception as e:
        raise BadRequest("Success must be a float (%s)" % str(e))
    if success < 0:
        raise BadRequest("Success must be positive (%s)" % str(success))
    try:
        filesize_avg = float(input_dict.get("filesize_avg", 0))
    except Exception as e:
        raise BadRequest("Filesize_avg must be a float (%s)" % str(e))
    if filesize_avg < 0:
        raise BadRequest("Filesize_avg must be positive (%s)" % str(filesize_avg))
    try:
        filesize_stddev = float(input_dict.get("filesize_stddev", 0))
    except Exception as e:
        raise BadRequest("Filesize_stddev must be a float (%s)" % str(e))
    if filesize_stddev < 0:
        raise BadRequest("Filesize_stddev must be positive (%s)" % str(filesize_stddev))

    optimizer = Optimizer(
        source_se=source_se,
        dest_se=dest_se,
        datetime=current_time,
        ema=ema,
        active=active,
        nostreams=nostreams,
    )
    evolution = OptimizerEvolution(
        source_se=source_se,
        dest_se=dest_se,
        datetime=current_time,
        ema=ema,
        active=active,
        throughput=throughput,
        success=success,
        rationale=rationale,
        diff=diff,
        actual_active=actual_active,
        queue_size=queue_size,
        filesize_avg=filesize_avg,
        filesize_stddev=filesize_stddev,
    )

    for key, value in input_dict.items():
        setattr(evolution, key, value)
    for key, value in input_dict.items():
        setattr(optimizer, key, value)

    Session.merge(evolution)
    Session.merge(optimizer)
    try:
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return evolution, optimizer
