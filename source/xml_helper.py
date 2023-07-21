from xml.etree.ElementTree import Element


class XmlHelper:

    @staticmethod
    def get_descendants(element: Element, *tags):
        queue = [element]
        while queue:
            elem = queue.pop()
            if elem != element:
                yield elem
            elem.findall()
