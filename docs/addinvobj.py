#!python3
import pathlib
import argparse
import sphobjinv as soi


parser = argparse.ArgumentParser(
    description='Add/remove an item to an inventory file')
parser.add_argument('file')
parser.add_argument('role')
parser.add_argument('name')
parser.add_argument('uri', nargs='?')
parser.add_argument('--priority', '-p', nargs='?')
parser.add_argument('--dispname', '-d', nargs='?')
parser.add_argument('--rm', '-r', action='store_true')
parser.add_argument('--test', '-t', action='store_true')


if __name__ == '__main__':
    opts = parser.parse_args()
    domain, role = opts.role.split(':', 1)
    inv = soi.Inventory(opts.file)

    i = len(inv.objects)
    while i >= 0:
        i -= 1
        obj = inv.objects[i]
        if (obj.name, obj.domain, obj.role) == (opts.name, domain, role):
            if opts.rm:
                del inv.objects[i]
                continue
            if opts.uri:
                obj.uri = opts.uri
            if opts.priority:
                obj.priority = opts.priority
            if opts.dispname:
                obj.dispname = opts.dispname
            break

    else:
        if not opts.rm:
            inv.objects.append(soi.DataObjStr(
                name=opts.name, domain=domain, role=role, uri=opts.uri,
                priority=opts.priority or '1',
                dispname=opts.dispname or '-'
            ))

    with open(1, 'wb', closefd=False) as stdout:
        stdout.write(inv.data_file())

    if not opts.test:
        soi.writebytes(opts.file, soi.compress(inv.data_file(contract=True)))
