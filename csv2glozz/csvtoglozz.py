#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
The program takes (optionally segmented) CSV files as inputs, processes the segment information (the "&"s) if applicable, and outputs an (.ac, .aa) pair of Glozz files.

The output files contain:
	- the .ac file will contain the text attributes of the dialogue turns (without the '&', one turn on a line).
	- the .aa file will contain:
		- a pre-annotation in terms of:
			- dialogue information:
				- cut at dice rollings;
				- trades,
				- dice rollings,
				- resource gettings.
			- turn information:
				- borders (implicit)
				- Identifier
				- Timestamp
				- Emitter
				- Resources
				- Developments
			- segment (UDE) information:
				- borders (implicit)
				- Shallow dialogue act: Question | Request | Assertion
				- Task dialogue act: Offer | Counteroffer | Accept | Refusal | Strategic_comment | Other

Usage:
>>> ./csvtoglozz.py -f <CSV file name>

@note: The output file names are formed by appending the .ac and .aa extensions to the input CSV file basename.
Example: for an input filename like document1.soclog.seg.csv, the pair  (document1.ac, document1.aa) is generated.
@note: The program supports filenames with empty spaces in them.
'''
import csv, sys, codecs
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
import datetime, time
from prettifyxml import prettify
import copy

root = Element('annotations', {'version':'1.0', 'encoding':'UTF-8', 'standalone':'no'})
root.append(Comment('Generated by csvtoglozz.py'))

import argparse
parser = argparse.ArgumentParser(description = '')
parser.add_argument('-f', '--file', dest = 'file', nargs = '+', help = "specify input file")
args = parser.parse_args(sys.argv[1:])
filename = ' '.join(args.file)

print filename

incsvfile = codecs.open(filename, 'rt')
csvreader = csv.reader(incsvfile, delimiter='\t')
firstcsvrow = csvreader.next()
dialoguetext = ' ' # for the .ac file
i=0
nb_dialogues = 0
dialog_leftborders = []
dialog_rightborders = []
csvrows = []
r_old = 0
for csvrow in csvreader:
	csvrows.append(csvrow)
for r in range(0,len(csvrows)):
	i += 1
	if csvrows[r] != firstcsvrow:
		try:
			the_row = copy.copy(csvrows[r])
			if len(the_row) >= 6 and len(the_row) < 8:
				padding = [''] * (8 - len(the_row))
				the_row.extend(padding)
			[curr_turn_id, curr_turn_timestamp, curr_turn_emitter, curr_turn_res, curr_turn_builds, curr_turn_text, curr_turn_annot, curr_turn_comment] = the_row
		except ValueError:
			print >> sys.stderr, "Error on row %d: %s" % (i, the_row)
			raise
	if curr_turn_emitter != "Server":
		dialoguetext +=curr_turn_id+' : '+curr_turn_emitter+' : '
		seg_leftborders = [len(dialoguetext)-1]
		seg_rightborders = [] # For dealing with ampersands which stand for segments' right borders
		# .ac buffer
		dialoguetext +=curr_turn_text+' '
		#dialog_leftborders = [0]
		#dialog_rightborders = [len(dialoguetext)-1]
		nosegs = 1
		for d in dialoguetext:
			if d == '&':
				nosegs += 1
				seg_rightborders.append(dialoguetext.index(d))
				if len(seg_rightborders) >= 1:
					seg_leftborders.append(seg_rightborders[-1])
				dialoguetext = dialoguetext[:dialoguetext.index(d)]+dialoguetext[dialoguetext.index(d)+1:]
		seg_rightborders.append(len(dialoguetext)-1)
		for t in curr_turn_text:
			if t == '&':
				curr_turn_text = curr_turn_text[:curr_turn_text.index(t)]+curr_turn_text[curr_turn_text.index(t)+1:]
		# .aa typographic annotations
		typunit = SubElement(root, 'unit', {'id':'stac_'+str(-i)})
		typmetadata = SubElement(typunit, 'metadata')
		typauthor = SubElement(typmetadata, 'author')
		typauthor.text='stac'
		typcreation_date = SubElement(typmetadata, 'creation-date')
		typcreation_date.text = str(-i)
		typlast_modif = SubElement(typmetadata, 'lastModifier')
		typlast_modif.text = 'n/a'
		typlast_modif_date = SubElement(typmetadata, 'lastModificationDate')
		typlast_modif_date.text = '0'
		typcharact = SubElement(typunit, 'characterisation')
		typeltype = SubElement(typcharact, 'type')
		typeltype.text = 'paragraph'
		typelfset = SubElement(typcharact, 'featureSet')
		typpos = SubElement(typunit, 'positioning')
		typstartpos = SubElement(typpos, 'start')
		if dialoguetext.index(curr_turn_text) != 0:
			typactualstpos = SubElement(typstartpos, 'singlePosition', {'index':str(len(dialoguetext)-len(curr_turn_text)-len(curr_turn_id)-len(curr_turn_emitter)-1-6)})
		else:
			typactualstpos = SubElement(typstartpos, 'singlePosition', {'index':str(0)})
		typendpos = SubElement(typpos, 'end')
		typactualendpos = SubElement(typendpos, 'singlePosition', {'index':str(len(dialoguetext)-1)})
		# .aa actual pre-annotations (Turn ID, Timestamp, Emitter)
		# a "Dialogue" Unit should be added, that is, Turns between Server's contributions containing "rolled"
		unit = SubElement(root, 'unit', {'id':'stac_'+str(int(time.mktime(datetime.datetime.now().timetuple())+i))})
		metadata = SubElement(unit, 'metadata')
		author = SubElement(metadata, 'author')
		author.text='stac'
		creation_date = SubElement(metadata, 'creation-date')
		creation_date.text = str(int(time.mktime(datetime.datetime.now().timetuple())+i))
		last_modif = SubElement(metadata, 'lastModifier')
		last_modif.text = 'n/a'
		last_modif_date = SubElement(metadata, 'lastModificationDate')
		last_modif_date.text = '0'
		charact = SubElement(unit, 'characterisation')
		eltype = SubElement(charact, 'type')
		eltype.text = 'Turn'
		elfset = SubElement(charact, 'featureSet')
		elfID = SubElement(elfset, 'feature', {'name':'Identifier'})
		elfID.text = curr_turn_id
		elfTimestamp = SubElement(elfset, 'feature', {'name':'Timestamp'})
		elfTimestamp.text = curr_turn_timestamp
		elfEmitter = SubElement(elfset, 'feature', {'name':'Emitter'})
		elfEmitter.text = curr_turn_emitter
		elfResources = SubElement(elfset, 'feature', {'name':'Resources'})
		elfResources.text = curr_turn_res.split("; unknown=")[0]
		elfBuildups = SubElement(elfset, 'feature', {'name':'Developments'})
		# To parse and (re)present in a suitable manner !
		curr_parsed_turn_builds = ""
		if len(curr_turn_builds) > 0:
			for item in curr_turn_builds.split("];"):
				if ']' not in item:
					item += ']'
				curr_parsed_turn_builds += item.split("=")[0]
				curr_parsed_turn_builds += "="
				curr_parsed_turn_builds += str(len(set(eval(item.split("=")[1].replace("; ", ",")))))
				curr_parsed_turn_builds += "; "
		curr_parsed_turn_builds = curr_parsed_turn_builds.strip("; ")
		#print curr_parsed_turn_builds
		elfBuildups.text = curr_parsed_turn_builds
		elfComments = SubElement(elfset, 'feature', {'name':'Comments'})
		elfComments.text = 'Please write in remarks...'
		pos = SubElement(unit, 'positioning')
		startpos = SubElement(pos, 'start')
		if dialoguetext.index(curr_turn_text) != 0:
			actualstpos = SubElement(startpos, 'singlePosition', {'index':str(len(dialoguetext)-len(curr_turn_text)-len(curr_turn_id)-len(curr_turn_emitter)-1-6)})
		else:
			actualstpos = SubElement(startpos, 'singlePosition', {'index':str(0)})
		endpos = SubElement(pos, 'end')
		actualendpos = SubElement(endpos, 'singlePosition', {'index':str(len(dialoguetext)-1)})
		# Segments information
#		print seg_leftborders
#		print seg_rightborders
#		print nosegs
#		print csvrows[r]
#		print "##"
		if len(seg_leftborders) == len(seg_rightborders):
			for k in range(0,len(seg_leftborders)):
				segment = SubElement(root, 'unit', {'id':'stac_'+str(int(time.mktime(datetime.datetime.now().timetuple())+10000+k))})
				smetadata = SubElement(segment, 'metadata')
				sauthor = SubElement(smetadata, 'author')
				sauthor.text='stac'
				screation_date = SubElement(smetadata, 'creation-date')
				screation_date.text = str(int(time.mktime(datetime.datetime.now().timetuple())+10000*i+k))
				slast_modif = SubElement(smetadata, 'lastModifier')
				slast_modif.text = 'n/a'
				slast_modif_date = SubElement(smetadata, 'lastModificationDate')
				slast_modif_date.text = '0'
				scharact = SubElement(segment, 'characterisation')
				seltype = SubElement(scharact, 'type')
				seltype.text = 'Segment'
				selfset = SubElement(scharact, 'featureSet')
				spos = SubElement(segment, 'positioning')
				sstartpos = SubElement(spos, 'start')
				sactualstpos = SubElement(sstartpos, 'singlePosition', {'index':str(seg_leftborders[k]+1)})
				sendpos = SubElement(spos, 'end')
				sactualendpos = SubElement(sendpos, 'singlePosition', {'index':str(seg_rightborders[k])})
	if curr_turn_emitter == "Server" and "rolled a" in curr_turn_text: # dialogue right boundary
	# hence, a dialogue is between the beginning and such a text (minus server's turns), or between such a text + 1 and another such text (minus server's turns).
		dice_rollings = []
		gets = []
		trades = ''
		#trades = []
		for rr in range(r+1,len(csvrows)):
			if csvrows[rr][2] == 'Server':
				if 'rolled a' in csvrows[rr][5]:
					# append to Dice_rolling feature values
					dice_rollings.append(csvrows[rr][5])
				if 'gets' in csvrows[rr][5]:
					# append to Gets feature values
					gets.append(csvrows[rr][5])
			else:
				break
		#print "r_old : " + str(r_old)
		for rrr in range(r, r_old-1, -1):
			if csvrows[rrr][2] == 'Server' and 'traded' in csvrows[rrr][5]:
				# append to Trades feature values
				trades = csvrows[rrr][5]
				break
#		print nb_dialogues
		#print dialog_leftborders
		#print dialog_rightborders
		r_old = r
		if nb_dialogues == 0:
			dialog_leftborders = [0]
			dialog_rightborders = [len(dialoguetext)-1]
		else:
			dialog_leftborders.append(dialog_rightborders[-1])
			dialog_rightborders.append(len(dialoguetext)-1)
		nb_dialogues += 1
		# Generate the actual annotation !
		if dialog_leftborders[-1] != dialog_rightborders[-1]:
			dialogue = SubElement(root, 'unit', {'id':'stac_'+str(int(time.mktime(datetime.datetime.now().timetuple())+100000+nb_dialogues))})
			dmetadata = SubElement(dialogue, 'metadata')
			dauthor = SubElement(dmetadata, 'author')
			dauthor.text='stac'
			dcreation_date = SubElement(dmetadata, 'creation-date')
			dcreation_date.text = str(int(time.mktime(datetime.datetime.now().timetuple())+100000*i+nb_dialogues))
			dlast_modif = SubElement(dmetadata, 'lastModifier')
			dlast_modif.text = 'n/a'
			dlast_modif_date = SubElement(dmetadata, 'lastModificationDate')
			dlast_modif_date.text = '0'
			dcharact = SubElement(dialogue, 'characterisation')
			deltype = SubElement(dcharact, 'type')
			deltype.text = 'Dialogue'
			delfset = SubElement(dcharact, 'featureSet')
			delfDiceroll = SubElement(delfset, 'feature', {'name':'Dice_rolling'})
			delfDiceroll.text = curr_turn_text
			# extra rollings
			if len(dice_rollings) >= 1:
				for roll in range(0,len(dice_rollings)):
					delfDiceroll.text += ' '+dice_rollings[roll]
			delfGets = SubElement(delfset, 'feature', {'name':'Gets'})
			delfGets.text = ''
			# extra gets
			if len(gets) >= 1:
				for get in range(0,len(gets)):
					delfGets.text += ' '+gets[get]
			delfTrades = SubElement(delfset, 'feature', {'name':'Trades'})
			delfTrades.text = ''
			# extra trades
			#if len(trades) >= 1:
			#	for trade in range(0,len(trades)):
			#		delfTrades.text += ' '+trades[trade]
			delfTrades.text = trades
			dpos = SubElement(dialogue, 'positioning')
			dstartpos = SubElement(dpos, 'start')
			dactualstpos = SubElement(dstartpos, 'singlePosition', {'index':str(dialog_leftborders[-1])})
			dendpos = SubElement(dpos, 'end')
			dactualendpos = SubElement(dendpos, 'singlePosition', {'index':str(dialog_rightborders[-1])})
# last dialogue : only if it doesn't end in a Server's statement !!

if len(dialog_rightborders) == 0 or dialog_rightborders[-1] != len(dialoguetext)-1:
	dialogue = SubElement(root, 'unit', {'id':'stac_'+str(int(time.mktime(datetime.datetime.now().timetuple())+100000+nb_dialogues+1))})
	dmetadata = SubElement(dialogue, 'metadata')
	dauthor = SubElement(dmetadata, 'author')
	dauthor.text='stac'
	dcreation_date = SubElement(dmetadata, 'creation-date')
	dcreation_date.text = str(int(time.mktime(datetime.datetime.now().timetuple())+100000*i+nb_dialogues+1))
	dlast_modif = SubElement(dmetadata, 'lastModifier')
	dlast_modif.text = 'n/a'
	dlast_modif_date = SubElement(dmetadata, 'lastModificationDate')
	dlast_modif_date.text = '0'
	dcharact = SubElement(dialogue, 'characterisation')
	deltype = SubElement(dcharact, 'type')
	deltype.text = 'Dialogue'
	delfset = SubElement(dcharact, 'featureSet')
	dpos = SubElement(dialogue, 'positioning')
	dstartpos = SubElement(dpos, 'start')
	if len(dialog_leftborders) >= 1:
		dactualstpos = SubElement(dstartpos, 'singlePosition', {'index':str(dialog_leftborders[-1])})
	else:
		dactualstpos = SubElement(dstartpos, 'singlePosition', {'index':str(0)})
	dendpos = SubElement(dpos, 'end')
	dactualendpos = SubElement(dendpos, 'singlePosition', {'index':str(len(dialoguetext))})
#for b in range(0,len(dialog_leftborders)):
#	print ">>>>>>>>>>>"
#	print dialoguetext[dialog_leftborders[b]:dialog_rightborders[b]]
#	print "<<<<<<<<<<<"

basename=filename.split(".")[0]
outtxtfile = codecs.open(basename+".ac", "w")
outtxtfile.write(dialoguetext)
outtxtfile.close()
outxmlfile = codecs.open(basename+".aa", "w", "ascii")
outxmlfile.write(prettify(root))
outxmlfile.close()
