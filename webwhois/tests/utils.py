import re

from django.http.response import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.utils.encoding import smart_text
from lxml import etree, html


def apply_patch(case, patcher):
    """
    Add patcher into cleanup, start it and return it.

    Examples:
        apply_patch(self, patch('module'))
    or in subclass of GingerAssertMixin:
        self.apply_patch(patch('module'))
        mocked = self.apply_patch(patch('module', mock))
    """
    if hasattr(patcher, "start"):
        start, stop = patcher.start, patcher.stop
    else:
        start, stop = patcher.enable, patcher.disable
    case.addCleanup(stop)
    return start()


def transform_to_text(node):
    "Transform text content of the node and all its descendants to the string."
    return "".join(node.xpath(".//text()"))


def transform_to_html(node):
    "Transform the node to the string with html tags together with attributes and text inside."
    if isinstance(node, etree.ElementBase):
        node = smart_text(html.tostring(node, encoding="UTF-8"))
    return node


class WebwhoisAssertMixin(object):
    """
    Usage:
        response = self.client.get(reverse("admin:academy_registration_change", args=(1,)))
        self.assertXpathEqual(response, "//input[@type='text']/@name", ['first_name', 'last_name'])
        self.assertCssSelectEqual(response, "div.field-link_course div a", [u"Text..."], self.transform_to_text)
        self.assertCssSelectEqual(response, "div.field-text_regdate div", [u"<div>01.04.2014 16:05</div>"])
    """
    _parsed_response = {}

    def _finish_assert(self, query_result, values, transform, normalize):
        """
        Finish assertion of result of selection (css, xpath).
        Parameter `query_result` can be one of the type: list, float, bool.
        """
        if isinstance(query_result, list):
            query_result = [transform(element) for element in query_result]
            values = list(values)
        else:
            query_result = transform(query_result)

        if normalize:
            if isinstance(query_result, list):
                query_result = [self.normalize_spaces(element) for element in query_result]

        self.assertEqual(query_result, values)

    def assertXpathEqual(self, response, selector, values, transform=transform_to_html, normalize=True):
        """
        Asserts that a xpath selector `selector` selects a particular list of `values` values from `response` content.
        `response` can be one of the type: str, unicode, HttpResponse, StreamingHttpResponse.

        Attribute `values` can be one of the type: list of strings, number, bool.

        The comparison of the selected elements of content and values is performed using the function `transform`;
        by default each element is serialized to string using `lxml.html.tostring()`. Any other callable can be used
        if `lxml.html.tostring()` doesn't provide a unique or helpful comparison.

        If attribute `normalize` is True (default), all white characters (nonprintable) are ''normalized''.
        It means that characters CR, LF, TAB are replaced by the SPACE and redundant and leading/trailing spaces
        are removed.
        """
        self._finish_assert(self._get_parsed_doctree(response).xpath(selector), values, transform, normalize)

    def assertCssSelectEqual(self, response, selector, values, transform=transform_to_html, normalize=True):
        """
        Asserts that a css selector `selector` selects a particular list of `values` values from `response` content.
        `response` can be one of the type: str, unicode, HttpResponse, StreamingHttpResponse.

        Attribute `values` must be a list of strings.

        The comparison of the selected elements of content and values is performed using the function `transform`;
        by default each element is serialized to string using `lxml.html.tostring()`. Any other callable can be used
        if `lxml.html.tostring()` doesn't provide a unique or helpful comparison.

        If attribute `normalize` is True (default), all white characters (nonprintable) are ''normalized''.
        It means that characters CR, LF, TAB are replaced by the SPACE and redundant and leading/trailing spaces
        are removed.
        """
        self._finish_assert(self._get_parsed_doctree(response).cssselect(selector), values, transform, normalize)

    transform_to_html = staticmethod(transform_to_html)
    transform_to_text = staticmethod(transform_to_text)  # and use it as self.transform_to_text()
    apply_patch = apply_patch

    def _get_parsed_doctree(self, response):
        """
        Parse HTML document into etree. Response must be one of the type:
        str, unicode, HttpResponse, StreamingHttpResponse.
        """
        if isinstance(response, (str, unicode)):
            response = HttpResponse(response)
        elif not isinstance(response, (HttpResponse, StreamingHttpResponse)):
            raise TypeError("Response in not type of HttpResponseBase.")
        elif isinstance(response, HttpResponseRedirect):
            raise TypeError("Response can not be a type of HttpResponseRedirect.")

        if isinstance(response, StreamingHttpResponse):
            content = b''.join(response.streaming_content)
        else:
            content = response.content

        doc = self._parsed_response.get(content)
        if doc is not None:
            return doc

        self._parsed_response[content] = html.fromstring(
            content,
            parser=html.HTMLParser(recover=True, encoding=response._charset),
        )

        return self._parsed_response[content]

    @staticmethod
    def normalize_spaces(value):
        """
        Removes leading and trailing spaces from the specified string, and replaces
        all internal sequences of white space with one.

        Example: normalize-space('   The  \r\n\t  BODY   \r\n')
        Result: 'The BODY'

        fn = http://www.w3.org/2005/xpath-functions
        fn:normalize-space(string)
        http://www.w3schools.com/xpath/xpath_functions.asp
        """
        if isinstance(value, html.HtmlElement):
            return "<Element %s at 0x...>" % value.tag
        return re.sub("\s+", " ", value).strip()
