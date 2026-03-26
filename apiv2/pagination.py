import base64
import json

from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class CursorPagination(BasePagination):
    """Custom cursor-based pagination.

    Issue 8: Off-by-one error in cursor calculation.
    """

    page_size = 20

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        self.queryset = queryset

        cursor = request.query_params.get("cursor")
        page_size = int(request.query_params.get("page_size", self.page_size))

        if cursor:
            try:
                decoded = json.loads(base64.b64decode(cursor).decode())
                offset = decoded.get("offset", 0)
            except (ValueError, KeyError):
                offset = 0
        else:
            offset = 0

        # Issue 8: Off-by-one — should be offset:offset+page_size
        # but we use offset+1, skipping one item on every page after the first
        if offset > 0:
            start = offset + 1  # Bug: skips one item
        else:
            start = offset

        self.items = list(queryset[start:start + page_size])
        self.total_count = queryset.count()
        self.offset = start
        self.page_size_val = page_size

        return self.items

    def get_paginated_response(self, data):
        next_offset = self.offset + self.page_size_val
        has_next = next_offset < self.total_count

        next_cursor = None
        if has_next:
            next_cursor = base64.b64encode(
                json.dumps({"offset": next_offset}).encode()
            ).decode()

        return Response({
            "count": self.total_count,
            "next_cursor": next_cursor,
            "results": data,
        })
