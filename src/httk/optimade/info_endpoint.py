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

from httk import __version__ as httk_version
from .httk_entries import httk_entry_info, httk_all_entries
from .versions import optimade_supported_versions
from .meta import generate_meta

def generate_info_endpoint_reply(request):
    """
    This just returns a hardcoded introspection string.
    """
    available_api_versions = []
    for ver in optimade_supported_versions:
        available_api_versions += [{'url': optimade_supported_versions[ver], 'version': request['baseurl'] + ver }]

    response = {
        "data": [
            {
                "id": "/",
                "type": "info",
                "attributes": {
                    "api_version": request['version'],
                    "available_api_versions": available_api_versions,
                    "formats": [
                        "json"
                    ],
                    "entry_types_by_format": {
                        "json": [
                            "structure",
                        ],
                    },
                    "available_endpoints": [
                        "info",
                        "links",
                        "structures"
                    ],
                    "is_index": False,
                }
            }
        ],
        "meta": generate_meta(request, 1)
    }
    return response


def generate_entry_info_endpoint_reply(request, entry):

    return {
        "data": {
            "description":httk_entry_info[entry]["description"],
            "properties":
                dict([(x,{
                    "description":httk_entry_info[entry]["properties"][x]["description"]
                }) for x in httk_entry_info[entry]["properties"]]),
            "formats": ["json"],
            "output_fields_by_format": {
                "json": [x for x in httk_entry_info[entry]["properties"]]
            }
        },
        "meta": generate_meta(request, 1)
    }


def generate_base_endpoint_reply(request):

    return """<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Optimate Endpoint</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <p>This is an <a href="https://www.optimade.org">OPTIMADE</a> base URL which can be queried with an OPTIMADE client.</p>
        <p>OPTIMADE version:"""+request['version']+"""</p>
    </body>
</html>
"""


def generate_versions_endpoint_reply(request):

    return """version
1
"""

def generate_links_endpoint_reply(request, links):
    #TODO: Fix invalid json example in optimade specification
    return {
        "data": [
                  {
                      "type": "links",
                      "id": x["id"],
                      "attributes": dict([(y,x[y]) for y in x if y != "id"]),
                  }
                for x in links] +
                  [
                    {
                        "type": "links",
                        "id": "optimade",
                        "attributes": {
                            "name": "Materials Consortia",
                            "description": "List of OPTIMADE providers maintained by the Materials Consortia organisation",
                            "base_url": "https://providers.optimade.org",
                            "homepage": "https://optimade.org",
                            "link_type": "providers"
                        }
                    }
                  ]
    }
