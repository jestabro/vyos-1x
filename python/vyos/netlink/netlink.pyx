# Copyright 2021 VyOS maintainers and contributors <maintainers@vyos.io>
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

from libc.string cimport memcpy, memset
from cython.operator cimport dereference
cimport netlink

cpdef nlmsghdr get_header(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef nlmsghdr hdr = dereference(<nlmsghdr*>buf_ptr)
    return hdr

# N. B. members must be accessed explicitly, due to issue with padding
# member (cf. comments in netlink.pxd).
cpdef (unsigned short, int, unsigned int, unsigned int) get_ifinfomsg(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef ifinfomsg ifi = dereference(<ifinfomsg*>buf_ptr)
    return (ifi.ifi_type, ifi.ifi_index, ifi.ifi_flags, ifi.ifi_change)

cpdef rtattr get_rtattr(bytes buf):
    cdef const unsigned char[:] buf_view = buf
    cdef char* buf_ptr = <char*>&buf_view[0]
    cdef rtattr attr = dereference(<rtattr*>buf_ptr)
    return attr

cpdef int Rta_Align(int leng):
    return RTA_ALIGN(leng)

cpdef int Nlmsg_Align(int leng):
    return NLMSG_ALIGN(leng)

cpdef bint Rta_Ok(rtattr attr, int alen):
    return RTA_OK(&attr, alen)

cpdef bytes Ifla_Rta(bytes buf):
    shift = NLMSG_ALIGN(sizeof(ifinfomsg))
    shift_buf = buf[shift:]
    return shift_buf

cpdef bytes Ifa_Rta(bytes buf):
    shift = NLMSG_ALIGN(sizeof(ifaddrmsg))
    shift_buf = buf[shift:]
    return shift_buf

cpdef bytes Nlmsg_Data(bytes buf):
    shift_buf = buf[NLMSG_HDRLEN:]
    return <bytes>shift_buf

cpdef bytes Rta_Data(bytes buf, int leng):
    cdef bytes ret = buf[RTA_LENGTH(0):leng]
    return ret
