#!/usr/bin/env python3
import glob
import os
import shutil

HOME_DIR = os.environ['HOME']


def install():
    symlinks = glob.glob('*.symlink')
    back_all = False
    skip_all = False
    over_all = False
    for source in symlinks:
        filename, _ = source.split('.')
        dest = HOME_DIR + '/.' + filename

        print('Installing file %s' % filename)

        if os.path.exists(dest):
            if not (back_all or skip_all or over_all):
                print('File %s exists.' % dest)
                print('Pick Action:')
                print('[s/S]kip /All')
                print('[o/O]verwrite /All')
                print('[b/B]ack_up /All')
                ans = input()

                if ans == 'S':
                    skip_all = True
                elif ans == 'O':
                    over_all = True
                elif ans == 'B':
                    back_all = True

            if skip_all or ans == 's':
                continue
            elif over_all or ans == 'o':
                try:
                    os.remove(dest)
                except Exception:
                    shutil.rmtree(dest)
            elif back_all or ans == 'b':
                shutil.move(dest, dest + '.back')
        # Check for broken symlinks
        elif os.path.lexists(dest):
            os.unlink(dest)

        # Create the link
        os.symlink(os.path.realpath(source), dest)

if __name__ == '__main__':
    install()
