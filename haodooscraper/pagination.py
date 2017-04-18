from math import ceil


class Pagination(object):
    """
    Pagination
    @param page specified page.
    @param per_page How many items to display in page.
    @param items data.
    """
    def __init__(self, page, per_page, total_count, items):
        if page < 1:
            self.page = 1
        else:
            self.page = page
        self.per_page = per_page
        self.total_count = total_count
        self._items = items
        if self.page > self.pages:
            self.page = self.pages

    @property
    def pages(self):
        """
        Count pages.
        """
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        """
        Has previous page?
        """
        return self.page > 1

    @property
    def has_next(self):
        """
        Has next page?
        """
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """
        Iterate pages.
        """
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
                    (num > self.page - left_current - 1 and
                     num < self.page + right_current) or \
                    num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def iter_each_pages(self):
        last = 0
        for num in range(1, self.pages + 1):
            if last + 1 != num:
                yield None
            yield num
            last = num

    def items(self):
        """
        Return the items in specified page.
        """
        for item in self._items:
            yield item
