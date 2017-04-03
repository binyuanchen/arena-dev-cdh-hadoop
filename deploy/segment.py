#!/usr/bin/env python

class NumericSegment(object):
    def __init__(self, s=None):
        # checking and breaking down: '1-5,6,7,8-10' => [[1,5], [6], [7], [8,10]]
        # but rejecting input in wrong order, such as '1-5,3' or '1,5,6-7,4' etc
        self.intervals = []
        largest=-1
        sections = s.split(',')
        for section in sections:
            points=section.split('-')
            if len(points) > 2:
                raise RuntimeError('section %s is illegal' % section)
            elif len(points) == 0:
                raise RuntimeError('one section is empty')
            elif len(points) == 1:
                x = int(points[0])
                if x <= 0:
                    raise RuntimeError('section %s is illegal' % section)
                if x <= largest:
                    raise RuntimeError('section %s is illegal' % section)
                self.intervals.append([int(points[0])])
                largest = x
            else:
                # len == 2
                # '5-5' is not allowed too
                x = int(points[0])
                y = int(points[1])
                if x <= 0 or y <= 0 or x >= y or x <= largest:
                    raise RuntimeError('section %s is illegal' % section)
                self.intervals.append([x, y])
                largest = y

    def contains(self, v=None):
        if not isinstance(v, int):
            raise RuntimeError('value %s is not an int' % v)
        for interval in self.intervals:
            if v < interval[0]:
                return False
            elif v > (interval[0] if len(interval) == 1 else interval[1]):
                continue
            else:
                return True
        return False

    def below(self, v=None):
        if not isinstance(v, int):
            raise RuntimeError('value %s is not an int' % v)
        if len(self.intervals) == 0:
            return True
        last = self.intervals[len(self.intervals)-1]
        if (last[0] if len(last) == 1 else last[1]) <= v:
            return True
        return False

if __name__ == '__main__':
    ns = NumericSegment('1-3,5,8-9,11')
    print ns.intervals
    print ns.contains(4)
    print ns.contains(2)
    print ns.contains(9)
    print ns.contains(12)

    print ns.below(10)
    print ns.below(11)
    print ns.below(12)
