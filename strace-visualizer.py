#!/usr/bin/env python3

import argparse
import os
import re
from random import randint
from decimal import *
from PIL import Image, ImageDraw, ImageFont


def parseStraceOutput(input_file):
    msgEntries = []

    if not os.path.exists(input_file):
        print('Input file \"'+input_file+'\" does not exist!')
        return 1
    with open(input_file, 'r') as f:
        for line in f.readlines():
            line=line.rstrip()    # remove '\n' from the end of a string

            if 'clone(' in line:
                line=re.split(r'\s\s*(?![^()]*\))', line)
                msgEntries.append([
                    { "PID" : line[0].split('<',1)[0], "pidname" : line[0] },     # { <PID>, <PID+Name> }
                    'clone()',                                                    # <message name>
                    line[1],                                                      # <call's time> 
                    { "PID" : line[4].split('<',1)[0], "pidname" : line[4] },     # { <PID>, <PID+Name> } of child process
                    None,                                                         #  None (<syscall result>)
                    None  ])                                                      #  None (<params of syscall>)

            elif 'execve(' in line:
                line=re.split(r'\s\s*(?![^()]*\))', line)
                msgEntries.append([
                    { "PID" : line[0].split('<',1)[0], "pidname" : line[0] },     # { <PID>, <PID+Name> }
                    'execve()',                                                   # <message's name>
                    line[1],                                                      # <call's time> 
                    None,                                                         #  None ({ <PID>, <PID+Name> } of child process)
                    line[4],                                                      # <syscall result>
                    line[2]  ])                                                   # <params of syscall>

            elif 'exit(' in line:
                line=re.split(r'\s\s*(?![^()]*\))', line)
                msgEntries.append([
                    { "PID" : line[0].split('<',1)[0], "pidname" : line[0] },     # { <PID>, <PID+Name> }
                    'exit()',                                                     # <message's name>
                    line[1],                                                      # <call's time> 
                    None,                                                         #  None ({ <PID>, <PID+Name> } of child process)
                    line[4],                                                      # <syscall result>
                    None  ])                                                      #  None (<params of syscall>)

            elif '+++ exited with ' in line:
                line=re.split(r'\s\s*(?![^()]*\))', line)
                msgEntries.append([
                    { "PID" : line[0].split('<',1)[0], "pidname" : line[0] },     # { <PID>, <PID+Name> }
                    'exited',                                                     # <message's name>
                    line[1],                                                      # <call's time> 
                    None,                                                         #  None ({ <PID>, <PID+Name> } of child process)
                    None,                                                         #  None (<syscall result>)
                    None  ])                                                      #  None (<params of syscall>)

        # Fix timestamps
        t0 = Decimal(msgEntries[0][2])
        for entry in msgEntries:
            entry[2] = Decimal(entry[2]) - t0

        return msgEntries


def createLifeLines(msgEntries):
    lifeLines = []

    for i, msgEntry in enumerate(msgEntries):

        # Is there exist entry in lifeLines with the same <PID+Name> ?
        existingLifeLine=None
        for entry in lifeLines:
            if msgEntry[0]["pidname"] == entry[0]:
                existingLifeLine=entry
                break


        if not existingLifeLine:

            # Try to find entry in lifeLines with the same <PID> to set hierarchyLVL value.
            hierarchyLVL = 0
            samePIDlifeLine = 0   # 0 is only for first lifeLine.
            for entry in lifeLines:
                if msgEntry[0]["PID"] == entry[0].split('<',1)[0]:
                    hierarchyLVL = entry[1]
                    samePIDlifeLine = lifeLines.index(entry)
                    break

            # Add new entry in lifeLines for <PID+Name> from current msg entry.
            lifeLines.append([
                msgEntry[0]["pidname"],        # <PID+name>
                hierarchyLVL,                  # 
                samePIDlifeLine,               # <Index>  Point to entry in lifeLines. Parent lifeLine for current one.
                [i]  ])                        # <Index>  Point to entry in msgEntries

            if msgEntry[1] == 'clone()':

                # Add additional entry in lifeLines for child's <PID+Name> from current msg entry.
                lifeLines.append([
                    msgEntry[3]["pidname"],    # child's <PID+name>
                    hierarchyLVL+1,            # 
                    len(lifeLines)-1,          # <Index>  Point to entry in lifeLines. Parent lifeLine for current one.  
                    [i]  ])                    # <Index>  Point to entry in msgEntries

            elif msgEntry[1] == 'fork()':
                pass


        else:
            # Add index that point to entry in msgEntries into lifeLine with the same <PID+Name>
            existingLifeLine[3].append(i)

            if msgEntry[1] == 'clone()':

                # Add new one entry in lifeLines for child's <PID+Name> from current msg entry.
                lifeLines.append([
                    msgEntry[3]["pidname"],                   # child's <PID+name>
                    existingLifeLine[1]+1,                    # <hierarchy level> 
                    lifeLines.index(existingLifeLine),        # <Index>  Point to entry in lifeLines
                    [i]  ])                                   # <Index>  Point to entry in msgEntries

    return lifeLines


def determineCoordHeight(msgEntries):
    listCoordHeight = []
    offset = 30

    for i in range(0, len(msgEntries)):
        listCoordHeight.append( i * offset )

    return listCoordHeight


def fixHierarchyLvl(lifeLines, listCoordHeight):

    # sort lifeLines by hierarchyLVL to line with higher hierarchyLVL will be drawn later than lower ones
    #lifeLines.sort(key=lambda x: x[1])

    complete = False
    #complete = True 
    while not complete:
        complete = True

        for line1 in lifeLines:
            hLvlLine1 = line1[1]
            if hLvlLine1 == 0:
                continue

            yBeginLine1 = listCoordHeight[ line1[3][0]  ]
            yEndLine1   = listCoordHeight[ line1[3][-1] ]

            for line2 in lifeLines:
                hLvlLine2 = line2[1]
                if line1 != line2 and hLvlLine1 == hLvlLine2:
                    yBeginLine2 = listCoordHeight[ line2[3][0]  ]
                    yEndLine2   = listCoordHeight[ line2[3][-1] ]

                    if yBeginLine2 < yEndLine1 and yEndLine2 >= yBeginLine1:
                        line1[1] = hLvlLine1 + 1  # update hierarchy lvl for line1
                        complete = False

    return lifeLines


def random_colour():
    r = randint(0, 255)
    g = randint(0, 255)
    b = randint(0, 255)
    rand_color = (r, g, b)
    return rand_color


def drawImg(lifeLines, msgEntries, listCoordHeight, output_file):

    startCoordWidth, startCoordHeight = 50, 50
    offsetWidth = 30

    lineWidth = 3
    pointHalfWidth = 4

    descrTextFont = "Pillow/Tests/fonts/FreeMono.ttf"
    descrTextFontSize = 12
    descrTextColor = "white"

    # creating new Image object
    w = 2000
    h = startCoordHeight + max(listCoordHeight) + 30
    img = Image.new("RGB", (w, h))
    img1 = ImageDraw.Draw(img)

    maxHierarchyLvl = max([entry[1] for entry in lifeLines])

    for i, lifeLine in enumerate(lifeLines):

        #lineColor = "red"
        lineColor = random_colour()

        firstEvent         = msgEntries[lifeLine[3][0]][1]
        hierarchyLVL       = lifeLine[1]
        parentHierarchyLVL = lifeLines[lifeLine[2]][1]

        listOfEvents = lifeLine[3]

        coordHFirstEntry = listCoordHeight[ listOfEvents[0]  ]
        if (               len(lifeLine[3]) >  1           and    # If number of events in current lifeLine > 1     AND
            msgEntries[listOfEvents[-1]][1] != 'execve()'  ):     # last event in current lifeLine !=  'execve()'

            coordHLastEntry  = listCoordHeight[ listOfEvents[-1] ]
        else:
            # If there's only one event in current lifeLine we need to one more event to draw line.
            # Try to find next entry (after current) in msgEntries with the same <PID> (not <pidname>).
            currMsgEntry=msgEntries[listOfEvents[-1]]
            for j in range(int(listOfEvents[-1])+1, len(msgEntries)):
                if msgEntries[j][0]["PID"] == currMsgEntry[0]["PID"]:
                    coordHLastEntry  = listCoordHeight[j]
                    break

        if firstEvent == 'clone()'  and   hierarchyLVL != parentHierarchyLVL :  # condition for drawing fork

            # draw lines
            lineBeginX = startCoordWidth + offsetWidth * hierarchyLVL
            lineBeginY = startCoordHeight + coordHFirstEntry + offsetWidth/2
            lineEndX   =   lineBeginX
            lineEndY   = startCoordHeight + coordHLastEntry
            shape = [ (lineBeginX, lineBeginY), (lineEndX, lineEndY) ]
            img1.line(shape, fill = lineColor, width = lineWidth)

            # draw fork
            forklineBeginX = startCoordWidth + offsetWidth * parentHierarchyLVL
            forklineBeginY = startCoordHeight + coordHFirstEntry
            forklineEndX   = startCoordWidth + offsetWidth * hierarchyLVL - offsetWidth/2
            forklineEndY   =   forklineBeginY
            shape = [ (forklineBeginX, forklineBeginY), (forklineEndX, forklineEndY) ]
            img1.line(shape, fill = lineColor, width = lineWidth)

            x = startCoordWidth  + offsetWidth * hierarchyLVL - offsetWidth
            y = startCoordHeight + coordHFirstEntry
            img1.arc((x, y, x+offsetWidth, y+offsetWidth), start=270, end=360, fill=lineColor, width=lineWidth)

            # for each event
            for counter, eventIndex in enumerate(listOfEvents):

                # draw point (event)
                if counter == 0 :  pointX = startCoordWidth  + offsetWidth * parentHierarchyLVL
                else:              pointX = startCoordWidth  + offsetWidth * hierarchyLVL
                pointY = startCoordHeight + listCoordHeight[eventIndex]
                shape = (pointX-pointHalfWidth, pointY-pointHalfWidth, pointX+pointHalfWidth, pointY+pointHalfWidth)
                img1.ellipse(shape, fill = lineColor, outline="black")

                # draw description
                if counter != 0 :
                    descrTextX = pointX + maxHierarchyLvl * offsetWidth + 40
                    descrTextY = pointY
                    descrText = (
                        str(i)                               +'  '+    # Number of lifeLine                       
                        str(msgEntries[eventIndex][2])       +'  '+    # time
                        msgEntries[eventIndex][0]["pidname"] +'  '+    # PID+name 
                        msgEntries[eventIndex][1]            +'  '+    # event (syscall or message)
                        ('= '+str(msgEntries[eventIndex][4]) if msgEntries[eventIndex][4] != None else '') +'  '+    # result of syscall 
                        (     str(msgEntries[eventIndex][5]) if msgEntries[eventIndex][5] != None else '')        )  # param of syscall
                    fnt = ImageFont.truetype(descrTextFont, descrTextFontSize)
                    #img1.text( (descrTextX,descrTextY), descrText, font=fnt, fill=descrTextColor) 
                    img1.text( (descrTextX,descrTextY), descrText, font=fnt, fill=lineColor)

        else:

            # draw lines
            lineBeginX = startCoordWidth + offsetWidth * hierarchyLVL
            lineBeginY = startCoordHeight + coordHFirstEntry
            lineEndX   =   lineBeginX
            lineEndY   = startCoordHeight + coordHLastEntry
            shape = [ (lineBeginX, lineBeginY), (lineEndX, lineEndY) ]
            img1.line(shape, fill = lineColor, width = lineWidth)

            # draw points (events) 
            for eventIndex in listOfEvents:

                pointX = startCoordWidth  + offsetWidth * hierarchyLVL
                pointY = startCoordHeight + listCoordHeight[eventIndex]
                shape = (pointX-pointHalfWidth, pointY-pointHalfWidth, pointX+pointHalfWidth, pointY+pointHalfWidth)
                img1.ellipse(shape, fill = lineColor, outline="black")

                # draw description
                descrTextX = pointX + maxHierarchyLvl * offsetWidth + 40
                descrTextY = pointY
                descrText = (
                    str(i)                               +'  '+    # Number of lifeLine                       
                    str(msgEntries[eventIndex][2])       +'  '+    # time
                    msgEntries[eventIndex][0]["pidname"] +'  '+    # PID+name 
                    msgEntries[eventIndex][1]            +'  '+    # event (syscall or message)
                    ('= '+str(msgEntries[eventIndex][4]) if msgEntries[eventIndex][4] != None else '') +'  '+    # result of syscall 
                    (     str(msgEntries[eventIndex][5]) if msgEntries[eventIndex][5] != None else '')        )  # param of syscall
                fnt = ImageFont.truetype(descrTextFont, descrTextFontSize)
                #img1.text( (descrTextX,descrTextY), descrText, font=fnt, fill=descrTextColor) 
                img1.text( (descrTextX,descrTextY), descrText, font=fnt, fill=lineColor)

    if output_file:
        img.save(output_file)
    else:
        img.show()


def main():
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input-file", required=True, help="path to input file")
    ap.add_argument("-o", "--output-file", required=False, help="path to output file")
    args = vars(ap.parse_args())


    msgEntries      = parseStraceOutput(args["input_file"])

    lifeLines       = createLifeLines(msgEntries)
    listCoordHeight = determineCoordHeight(msgEntries)

    lifeLines       = fixHierarchyLvl(lifeLines, listCoordHeight)

    #for i,entry in enumerate(msgEntries):
    #    print("{}: {}".format(i, entry))
    #print('------------------------------')

    #for i,entry in enumerate(lifeLines):
    #    print("{}: {}".format(i, entry))
    #print('------------------------------')

    drawImg(lifeLines, msgEntries, listCoordHeight, args["output_file"])


if __name__ == '__main__':
    main()
