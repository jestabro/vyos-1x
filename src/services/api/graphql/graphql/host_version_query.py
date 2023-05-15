# Copyright 2023 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import jwt
import datetime
from typing import Any, Dict, Optional
from ariadne import ObjectType, UnionType
from graphql import GraphQLResolveInfo

from .. session.session import get_host_version
from .. import state

host_version_query = ObjectType("Query")

@host_version_query.field('HostVersion')
def host_version_resolver(obj: Any, info: GraphQLResolveInfo, data: Optional[Dict]=None):
    expose_host_version = bool(state.settings['app'].state.vyos_expose_host_version)

    if expose_host_version:
        if data is None:
            data = {}

        res = get_host_version()

        data['result'] = res
        return {
            "success": True,
            "data": data
        }

    return {
        "success": False,
        "errors": ['unauthenticated query of hostname/version not configured']
    }
