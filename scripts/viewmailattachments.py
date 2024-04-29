#! /usr/bin/env python3

# Take an mbox HTML message (e.g. from mutt), split it
# and rewrite it so it can be viewed in an external browser.
# Can be run from within a mailer like mutt, or independently
# on a single message file.
#
# Usage: viewhtmlmail.py email_message_file
#
# Inspired by John Eikenberry <jae@zhar.net>'s view_html_mail.sh
# which sadly no longer works, at least with mail from current Apple Mail.
#
# Copyright 2013-2022 by Akkana Peck. Share and enjoy under the GPL v2 or later.
# Contributions:
#   Holger Klawitter 2014: create a secure temp file and avoid temp mbox
#   Antonio Terceiro 2018: Allow piping directly from mutt.

# To use it from mutt, install it somewhere in your path,
# then put the following lines in your .muttrc:
# macro index <F9> "<pipe-message>~/bin/viewhtmlmail.py\n" "View HTML email in browser"
# macro pager <F9> "<pipe-message>~/bin/viewhtmlmail,ot\n" "View HTML email in browser"

# TESTING: Use the email file in test/files/htmlmail.eml.

import os, sys
import logging
import re
import time
import shutil
import email, mimetypes
from email.parser import BytesParser
from email.policy import default as default_policy
import subprocess
from collections import OrderedDict   # for python < 3.7


log = logging.getLogger(__name__)

################################################
# Some prefs:

# If IMAGE_VIEWER is set, a message that has no multipart/related
# images will use the image viewer rather than a browser window
# for images. To use a browser, set IMAGE_VIEWER = None.
IMAGE_VIEWER = "eog"
# IMAGE_VIEWER = None
IMAGE_VIEWER_ARGS = []   # For pho, don't use presentation mode

USE_WVHTML_FOR_DOC = False

# How many seconds do we need to wait for unoconv?
# It defaults to 6, but on a 64-bit machine that's not nearly enough.
# Even 10 often isn't enough.
UNOCONV_STARTUP_TIME = "14"

# A list of supported browsers, in order of preference.
BROWSERS = OrderedDict([
    ('google-chrome', {
        'ARGS': [  "--incognito" ],
        'CONVERT_PDF_TO_HTML': False,
    })
])

WORKING_BROWSER = "google-chrome"


def run_browser(browser, htmlfile):
    """Call a specific browser with the appropriate arguments.
       May raise various errors.
    """
    cmd = [ browser ]

    cmd += BROWSERS[browser]['ARGS']

    cmd.append("file://" + htmlfile)
    log.debug("Calling in background: %s", ' '.join(cmd))
    mysubprocess.call_bg(cmd)


def call_some_browser(htmlfile):
    """Try the list of browsers to find which one works."""
    global WORKING_BROWSER

    log.debug("Calling browser for file://%s", htmlfile)

    run_browser(WORKING_BROWSER, htmlfile)
    return

# Seconds to wait between refreshes when waiting for translated content
REDIRECT_TIMEOUT = 2

# End global prefs
################################################


def find_first_maildir_file(maildir):
    """Maildir: inside /tmp/mutttmpbox, mutt creates another level of
       directory, so the file will be something like /tmp/mutttmpbox/cur/1.
       So recurse into directories until we find an actual mail file.
       Return a full path to the filename.
    """
    for root, dirs, files in os.walk(maildir):
        for f in files:
            if not f.startswith('.'):
                return os.path.join(root, f)
    return None


MAX_FILENAME_LENGTH = 225

def sanitize_filename(badstr):
    """Sanitize a filename to make sure there's nothing dangerous, like ../
       Also make sure it's under MAX_FILENAME_LENGTH.
    """
    filename = ''.join([x for x in badstr if x.isalpha() or x.isdigit()
                      or x in '-_.'])
    if len(filename) > MAX_FILENAME_LENGTH:
        half = MAX_FILENAME_LENGTH // 2
        filename = filename[:half] + filename[-half:]

    return filename


def view_html_message(f, tmpdir):
    # Note: the obvious way to read a message is
    #   with open(f) as fp: msg = email.message_from_file(fp)
    # What the docs don't tell you is that that gives you an
    # email.message.Message, which is limited and poorly documented;
    # all the documentation assumes you have an email.message.EmailMessage,
    # but to get that you need the more complicated BytesParser method below.
    # The policy argument to BytesParser is mandatory: without it,
    # again, you'll get a Message and not an EmailMessage.
    if f:
        if os.path.isdir(f):
            # Maildir: f is a maildir like /tmp/mutttmpbox,
            # and inside it, for some reason, mutt creates another
            # level of directory named either cur or new
            # depending on whether the message is already marked read.
            # So we have to open the first file inside either cur or new.
            # In case mutt changes this behavior, let's take the first
            # non-dotfile inside the first non-dot directory.
            msg = None
            for maildir in os.listdir(f):
                with open(find_first_maildir_file(f), 'rb') as fp:
                    msg = BytesParser(policy=default_policy).parse(fp)
                    break
        else:
            # Mbox format: we assume there's only one message in the mbox.
            with open(f, 'rb') as fp:
                # msg = email.message_from_string(fp.read())
                msg = BytesParser(policy=default_policy).parse(fp)
    else:
        msg = BytesParser(policy=default_policy).parsebytes(sys.stdin.buffer.read())

    counter = 1
    filename = None
    filenames = set()
    subfiles = {}    # A dictionary mapping content-id to [filename, part]
    html_parts = []

    # For debugging:
    def print_part(part):
        log.debug("*** part:")   # parts are type email.message.Message
        log.debug("  content-type: %s", part.get_content_type())
        log.debug("  content-disposition: %s", part.get_content_disposition())
        log.debug("  content-id: %s", part.get('Content-ID'))
        log.debug("  filename: %s", part.get_filename())
        log.debug("  is_multipart? %s", part.is_multipart())

    def print_structure(msg, indent=0):
        """Iterate over an EmailMessage, printing its structure"""
        indentstr = ' ' * indent
        for part in msg.iter_parts():
            log.debug("%scontent-type: %s", indentstr, part.get_content_type())
            log.debug("%s  content-subtype: %s", indentstr, part.get_content_subtype())
            log.debug("%s  content-id: %s", indentstr, part.get('Content-ID'))
            log.debug("%scontent-disposition: %s", indentstr, part.get_content_disposition())
            log.debug("%sfilename: %s", indentstr, part.get_filename())
            log.debug("%sis_multipart? %s", indentstr, part.is_multipart())
            print_structure(part, indent=indent+2)

    print_structure(msg)

    for part in msg.walk():
        print_part(part)

        # multipart/* are just containers
        #if part.get_content_maintype() == 'multipart':
        if part.is_multipart() or part.get_content_type == 'message/rfc822':
            continue

        # Get the content id.
        # Mailers may use Content-Id or Content-ID (or, presumably, various
        # other capitalizations). So we can't just look it up simply.
        content_id = None
        for k in list(part.keys()):
            if k.lower() == 'content-id':
                # Remove angle brackets, if present.
                # part['Content-Id'] is unmutable -- attempts to change it
                # are just ignored -- so copy it to a local mutable string.
                content_id = part[k]
                if content_id.startswith('<') and content_id.endswith('>'):
                    content_id = content_id[1:-1]

                counter += 1

                break     # no need to look at other keys

        if part.get_content_subtype() == 'html':
            log.debug("Found an html part")
            if html_parts:
                log.debug("Eek, more than one html part!")
            html_parts.append(part)

        elif not content_id:
            log.debug("No Content-Id")

        # Use the filename provided if possible, otherwise make one up.
        filename = part.get_filename()

        if filename:
            filename = sanitize_filename(filename)
        else:
            # if DEBUG:
            #     print("No filename; making one up")
            ext = mimetypes.guess_extension(part.get_content_type())
            if not ext:
                # Use a generic bag-of-bits extension
                ext = '.bin'
            if content_id:
                filename = sanitize_filename('cid%s%s' % (content_id, ext))
            else:
                filename = 'part-%03d%s' % (counter, ext)

        # Some mailers, like gmail, will attach multiple images to
        # the same email all with the same filename, like "image.png".
        # So check whether we have to uniquify the names.
        if filename in filenames:
            orig_basename, orig_ext = os.path.splitext(filename)
            dedup_counter = 0
            while filename in filenames:
                dedup_counter += 1
                filename = "%s-%d%s" % (orig_basename, dedup_counter, orig_ext)

        filenames.add(filename)

        # If there's no content_id, use the uniquified filename, sans path.
        if not content_id:
            content_id = filename

        filename = os.path.join(tmpdir, filename)

        # Now save content to the filename, and remember it in subfiles.
        subfiles[content_id] = [ filename, part ]
        with open(filename, 'wb') as fp:
            fp.write(part.get_payload(decode=True))
            log.debug("wrote %s", filename)

        # print "%10s %5s %s" % (part.get_content_type(), ext, filename)

    log.debug("subfiles now: %s", subfiles)

    # We're done saving the parts. It's time to save the HTML part(s),
    # with img tags rewritten to refer to the files we just saved.
    embedded_parts = []
    for i, html_part in enumerate(html_parts):
        htmlfile = os.path.join(tmpdir, "viewhtml%02d.html" % i)
        fp = open(htmlfile, 'wb')

        # html_parts[i].get_payload() returns string, but it's apparently
        # in straight unicode and doesn't reflect the message's charset.
        # html_part.get_payload(decode=True) returns bytes,
        # which (I think) have been decoded as far as email transfer
        # (e.g. Content-Encoding: base64), which is not the same thing
        # as charset decoding.
        # (None of this is documented in the python3 email module;
        # there's no mention of get_payload() at all. Sigh.)

        htmlsrc = html_part.get_payload(decode=True)

        # Substitute all the filenames for content_ids:
        for sf_cid in subfiles:
            # Yes, yes, I know:
            # https://stackoverflow.com/questions/1732348/regex-match-open-tags-except-xhtml-self-contained-tags/
            # and this should be changed to use BeautifulSoup.
            log.debug("Replacing cid %s with %s", sf_cid, subfiles[sf_cid][0])
            newhtmlsrc = re.sub(b'cid: ?' + sf_cid.encode(),
                                b'file://' + subfiles[sf_cid][0].encode(),
                                htmlsrc, flags=re.IGNORECASE)
            if sf_cid not in embedded_parts and newhtmlsrc != htmlsrc:
                embedded_parts.append(sf_cid)
            htmlsrc = newhtmlsrc

        fp.write(htmlsrc)
        fp.close()
        log.debug("Wrote %s", htmlfile)

        # Now we have the file. Call a browser on it.
        call_some_browser(htmlfile)

    # Done with htmlparts.
    # Now handle any parts that aren't embedded inside HTML parts.
    # This includes conversions from Word or PDF, but also image attachments.
    log.debug("subfiles: %s", subfiles)
    log.debug("Parts already embedded: %s", embedded_parts)

    image_files = []
    for sfid in subfiles:
        log.debug("Part: %s", subfiles[sfid][0])
        part = subfiles[sfid][1]
        partfile = subfiles[sfid][0]    # full path
        fileparts = os.path.splitext(partfile)

        if sfid in embedded_parts:
            log.debug("%s was already embedded in html", partfile)
            continue

        if part.get_content_maintype() == "image":
            image_files.append(partfile)
            continue

        if part.get_content_maintype() == "application":
            if part.get_content_subtype() == "pdf" or partfile.endswith("pdf"):
                call_some_browser(partfile)

            subtype = part.get_content_subtype()
            log.debug("Application subtype: %s. Skipping...", subtype)
            continue

    if image_files:
        if IMAGE_VIEWER:
            log.debug("Calling %s on %s", IMAGE_VIEWER, image_files)
            cmd = [ IMAGE_VIEWER ] + IMAGE_VIEWER_ARGS + image_files
            mysubprocess.call_bg(cmd)
        else:
            for img in image_files:
                call_some_browser(img)


# For debugging:
class mysubprocess:
    @staticmethod
    def call(arr):
        log.debug("========= Calling: %s", str(arr))
        subprocess.call(arr)

    @staticmethod
    def call_bg(arr):
        log.debug("========= Calling in background: %s", str(arr))
        subprocess.Popen(arr, shell=False,
                         stdin=None,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    import tempfile

    import argparse

    parser = argparse.ArgumentParser(description="View HTML email in browser")
    parser.add_argument("mbox", nargs="?",
                        help="The file containing an RFC822 email."
                             " If omitted read from stdin.")
    parser.add_argument("-d", "--debug", default=False,
                        action="store_true", help="Debug logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level)

    tmpdir = tempfile.mkdtemp(prefix="muttviewmailattachemnts")
    view_html_message(args.mbox, tmpdir)

    #print("Deleting %s" % tmpdir)
    # shutil.rmtree(tmpdir)
