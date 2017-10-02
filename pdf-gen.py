from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import utils
from emojipy import Emoji
import os
import glob
import re
import json

def replace_with_emoji_pdf(text, size):
    text = Emoji.to_image(text)
    text = text.replace('class="emojione"', 'height=%s width=%s' %
                        (size, size))
    return re.sub(u'(alt=".{,5}")|([^\x00-\x7F]+)', '', text)

def getHeaderStyle():
    style = getSampleStyleSheet()
    normal = style['Normal']
    normal.alignment = TA_CENTER
    normal.fontName = 'Helvetica'
    normal.fontSize = 20
    normal.spaceBefore = 6
    normal.spaceAfter = 12
    return normal

def getNormalStyle():
    style = getSampleStyleSheet()
    normal = style['Normal']
    normal.alignment = TA_LEFT
    normal.fontName = 'Helvetica'
    normal.fontSize = 14
    normal.spaceBefore = 6
    normal.spaceAfter = 6
    normal.leading = 18
    return normal

def getCaptionStyle():
    style = getNormalStyle()
    style.fontSize = 16
    return style

def listFileFromDirectory():
    path = 'data/'
    for filename in os.listdir(path):
        usernameDir = os.path.join(path, filename)
        username = os.path.basename(usernameDir)
        Story = []
        Story.append(Paragraph('<b>%s</b>' % username, getHeaderStyle()))
        Story.append(Spacer(1, 12))

        for photo in sorted(glob.glob(os.path.join(usernameDir, '*.jpg'))):
            basename = os.path.splitext(photo)[0]
            textFile = basename + '.txt'
            photoFile = basename + '.jpg'

            with open(textFile) as f:
                content = json.loads(f.read())

            appendContentToPDF(username, Story, content, photoFile)

        doc = SimpleDocTemplate(username + ".pdf",pagesize=letter,
                                rightMargin=72,leftMargin=72,
                                topMargin=48,bottomMargin=36)
        doc.build(Story)

def appendContentToPDF(username, Story, content, photoFile):
    print (content)
    date = content['date']
    like = content['likes']
    location = '\U0001f4cc ' + content['location'] if content['location'] else ""
    location = '<font color="blue">' + replace_with_emoji_pdf(location, 14) + '</font>'
    caption = replace_with_emoji_pdf(content['caption'], 16)

    # add date on top left of the pdf
    Story.append(Paragraph(date, getNormalStyle()))

    # add location on top left of the pdf
    Story.append(Paragraph(location, getNormalStyle()))
    Story.append(Spacer(1, 12))

    # add images to the pdf
    img = utils.ImageReader(photoFile)
    width, height = img.getSize()
    aspect = height / float(width)
    im = Image(photoFile, 4*inch, 4*inch*aspect)
    im.hAlign = 'CENTER'
    Story.append(im)

    Story.append(Spacer(1, 12))

    # add likes to the pdf
    Story.append(Paragraph('<b>%s likes</b>' % like, getCaptionStyle()))

    # add caption to the pdf
    Story.append(Paragraph('<b>%s</b> %s' % (username, caption), getCaptionStyle()))

    Story.append(Spacer(1, 6))

    for comment in content['comments']:
        commenter = comment['person']
        commentContent = replace_with_emoji_pdf(comment['text'], 14)
        Story.append(Paragraph('<b>%s</b> %s' % (commenter, commentContent), getNormalStyle()))

    # new page
    Story.append(PageBreak())

listFileFromDirectory()
