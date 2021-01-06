#!/usr/bin/env python
#
#    The high-throughput toolkit (httk)
#    Copyright (C) 2012-2020 Rickard Armiento
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime

from httk.optimade.versions import optimade_default_version

def format_optimade_error(ex, representation, version=optimade_default_version):

    if isinstance(ex, OptimadeError):
        response_code = ex.response_code
        title = ex.response_msg
        detail = ex.content
    else:
        response_code = 500
        title = "Internal Server Error"
        detail = str(ex)

    response = {
        "errors": [
            {
                "status": response_code,
                "title": title,
                "detail": detail
            }
        ],
        "meta": {
            "query": {
                "representation": representation
            },
            "api_version": version,
            "more_data_available": False,
            # TODO: ADD "schema":
            "time_stamp": datetime.datetime.now().isoformat(),
            "data_returned": 0,
        }
    }

    return {'json_response': response, 'content_type':'application/vnd.api+json', 'response_code':response_code, 'response_msg':title, 'encoding':'utf-8'}

class OptimadeError(Exception):
    def __init__(self, message, response_code, response_message, longmsg=None):
        super(OptimadeError, self).__init__(message)
        self.response_code = response_code
        self.response_msg = response_message
        self.message = message
        self.long_message = longmsg
        self.content = longmsg if longmsg is not None else message
    pass

class TranslatorError(OptimadeError):
    pass

