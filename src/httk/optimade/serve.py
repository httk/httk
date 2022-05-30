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

import json

from httk.httkweb import webserver
from httk.optimade.process import process, process_init
from httk.optimade.httk_execute_query import httk_execute_query
from httk.optimade.error import format_optimade_error
from httk.optimade.validate import determine_optimade_version
from httk.optimade.versions import optimade_default_version

def _json_format(response):
    return json.dumps(response, indent=4, separators=(',', ': '), sort_keys=True)

def format_output(output):
    if output['content_type'] in [ 'application/vnd.api+json', 'application/json']:
        output['content'] = _json_format(output['json_response'])
    return output

def serve(store, config=None, port=80, baseurl = None, debug=False):

    if config is None:
        config = {}

    if "links" not in config:
        config["links"] = []

    if "provider" not in config:
        config["provider"] = {
            "name": "httk",
            "description": "This is a database hosted with the High-Throughput Toolkit (httk), for which the hoster has not specifically configured the provider.",
            "prefix": "httk"
        }

    if baseurl is not None:
        if not baseurl.endswith("/"):
            baseurl += "/"

    def query_function(entries, response_fields, unknown_response_fields, response_limit, response_offset, filter_ast=None, debug=False):
        return httk_execute_query(store, entries, response_fields, unknown_response_fields, response_limit, response_offset, filter_ast, debug)

    def httk_error_callback(request, ex, baseurl=baseurl):
        # If the user has configured a baseurl, use it and ignore what the server thinks it serves from
        if baseurl is not None:
            request['baseurl'] = baseurl
        try:
            version = determine_optimade_version(request)
        except Exception as e:
            output = format_optimade_error(ex, request, config, version=optimade_default_version)
            return format_output(output)
        try:
            output = format_optimade_error(ex, request, config, version=version)
            return format_output(output)
        except Exception as e:
            output = format_optimade_error(ex, request, config, version=optimade_default_version)
            return format_output(output)

    def httk_web_callback(request, baseurl=baseurl):
        # If the user has configured a baseurl, use it and ignore what the server thinks it serves from
        if baseurl is not None:
            request['baseurl'] = baseurl
        if request['relpath'] == '':
            request['relpath'] = 'index.html'

        version = determine_optimade_version(request)
        output = process(request, query_function, version, config, debug=debug)
        return format_output(output)

    if baseurl == None:
        if port == 80:
            baseurl="http://localhost/"
        else:
            baseurl="http://localhost:"+str(port)+"/"

    process_init(config, query_function, debug=debug)

    if not debug:
        webserver.startup(httk_web_callback, port=port, error_callback=httk_error_callback, debug=False)
    else:
        webserver.startup(httk_web_callback, port=port, debug=True)

if __name__ == "__main__":

    import httk, httk.db

    backend = httk.db.backend.Sqlite('../../../Tutorial/tutorial_data/tutorial.sqlite')
    store = httk.db.store.SqlStore(backend)

    config = {
      "links": [
        {
            "id": "index",
            "name": "omdb index",
            "description": "Index for omdb's OPTIMADE databases",
            "base_url": "https://optimade-index.openmaterialsdb.se",
            "homepage": "http://openmaterialsdb.se",
            "link_type": "root"
        },
      ]
    }

    serve(store, config, debug=True)
