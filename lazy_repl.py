from lazy_parser import Parser, pprint
import sys
import re
import collections
import math
import readline

REPL = False
WARN = False
READ='' # init for singleton file

# run expressions manually
# 10 3 5 - *
def rpn_exec( expr, memory, calls=[] ):

	ops = {
		'-': lambda x,y: x-y,
		'+': lambda x,y: x+y,
		'*': lambda x,y: x*y,
		'/': lambda x,y: x/y,
		'^': lambda x,y: x**y,
		'&': lambda x,y: float(int(x)&int(y)),
		'|': lambda x,y: float(int(x)|int(y)),
		'<': lambda x,y: 1.0 if x < y else 0.0,
		'>': lambda x,y: 1.0 if x > y else 0.0,
		'%': lambda x,y: x%y
	}
	uops = {
		'~': lambda x: -x,
		'!': lambda x: 1.0 if x==0 else 0.0
	}
	stack = [] + calls

	if not expr:
		return [None]

	if REPL: print( "EXEC: < %s >" % expr )

	queue = expr.copy()
	while queue:
		val = queue.pop(0)
		if type(val) is tuple:
			# print( val )
			key, params, body = val
			mem = memory.copy()
			# mem[ '%proc' ] = memory[ '%proc' ]

			if key == 'MACRO':
				mem['%macro'][params]( stack, body )
				continue

			if key == 'FUNC':
				for token in params[::-1]:
					if not stack:
						print( 'RUNTIME ERROR: expr: insufficient left-function params < %s >' % expr )
						return [None]
					mem[ token ] = [stack.pop()]
			elif key == 'RFUNC':
				for token in params:
					if not queue:
						print( 'RUNTIME ERROR: expr: insufficient right-function params < %s >' % expr )
						return [None]
					mem[ token ] = [queue.pop(0)]
			elif key == 'PROC':
				for token in params:
					try:
						mem[ token ] = memory[ token ]
					except:
						print( 'RUNTIME ERROR: expr: proc params not set < %s >' % params )
						return [None]

			repl_exec( body, mem )

			try:
				#stack.append( ... )
				# more lazy
				stack = rpn_exec( mem['%ret'], memory, stack.copy() )
			except:
				if WARN: print( 'RUNTIME WARN: rpn: no ret statement' )
				stack.append( 0.0 )

		elif val in uops.keys():
			if not stack:
				print( 'RUNTIME ERROR: expr: insufficient unary args < %s >' % expr )
				return [None]
			a = stack.pop()
			stack.append( uops[ val ](a) )
		elif val in ops.keys():
			if not len(stack) > 1:
				print( 'RUNTIME ERROR: expr: insufficient operation args < %s >' % expr )
				return [None]

			b, a = stack.pop(), stack.pop()
			stack.append( ops[ val ](a, b) )
		else:
			stack.append( float(val) )

	return stack

'''
tmp = procedure name
proc[ tmp ][0] = params list 
proc[ tmp ][1] = stmts list
'''
def expand_expr( expr, memory ):
	exec_list = []
	queue = expr.copy()

	# print( expr )
	while queue:
		i = queue.pop(0)
		# gross, handles already expanded exprs
		if type(i) is float or type(i) is int or type(i) is str:
			# print( i )
			exec_list.append( i )
			continue

		token = i[0]
		kind = i[1]
		if kind == 'ID':
			# print( "--",i )
			try:
				exec_list += expand_expr(memory[ i ], memory) # more lazy
				# exec_list += memory[ i ]
			except:
				if not i in memory[ '%proc' ].keys():
					print( 'RUNTIME ERROR: expand: <%s> not assigned: %s' % (i,expr) )
					# exit()
					continue

				# local_mem = memory.copy()
				# local_mem[ '%proc' ] = memory[ '%proc' ]

				key,_,func, params = memory[ '%proc' ][ i ] # more lazy, all of stmt
				# key,func, params = memory[ '%proc' ][ token ]
				if not type(params) is list:
					params = [ queue.pop(0) if queue else '' for i in range(params) ]

				exec_list.append( (key,func,params) )

				''' # not lazy approach
				for param, kind in memory[ '%proc' ][ token ][0]:
					try:
						local_mem[ param ] = memory[ param ]
					except:
						print( 'RUNTIME ERROR: expand: <%s> not assigned before func <%s>' % (param,token) )
						exit()
				repl_exec( memory[ '%proc' ][ token ][1], local_mem )
				try:
					exec_list = exec_list + local_mem['%ret']
				except:
					if WARN: print( 'RUNTIME WARN: expand: no ret statement' )
					exec_list.append( 0 )
				'''

		elif kind in ['FUNC','RFUNC']:
			exec_list.append( (i[1],i[2],i[3]) )

		# more already expanded help
		elif token in ['FUNC','MACRO']:
			exec_list.append( i )

		else:
			exec_list.append( token )

	# print( exec_list )
	return exec_list

# run as python code
def python_exec( string, memory ):
	try:
		exec( string, memory )
	except RuntimeError as e:
		print( 'RUNTIME ERROR: expression error', e )
		exit()

def repl_exec( program, memory ):
	for stmt in program:
		if stmt[0] in ['ASN',':ASN']:
			# repl_expr( '%s=%s'%(stmt[1][0], expand_expr(stmt[2][1])), memory )
			# print( stmt[1],'=',stmt[2][1] )
			# memory[ stmt[1] ] = expand_expr( stmt[2][1], memory )
			# resolve the names in return memory
			if stmt[0] == ':ASN':
				memory[ stmt[1] ] = rpn_exec( expand_expr( stmt[2][1], memory ), memory )
			else:
				# partially lazy
				if stmt[1] == '%ret':
					memory[ stmt[1] ] = expand_expr( stmt[2][1], memory )
				else:
					memory[ stmt[1] ] = stmt[2][1] # more lazy
			# print( stmt[0], stmt[1], memory[ stmt[1] ] )

		elif stmt[0] == 'EXPR':
			tmp = rpn_exec( expand_expr(stmt[1], memory), memory )
			if REPL: print( tmp )

		elif stmt[0] == 'LOOP':
			# print ( stmt[1][1], stmt[2][1] )
			# print( expand_expr(stmt[1][1], memory) )
			while rpn_exec( expand_expr(stmt[1][1], memory), memory )[-1] != 0:
				repl_exec( stmt[2][1], memory )

		elif stmt[0] == 'BRANCH':
			if rpn_exec( expand_expr(stmt[1][1], memory), memory )[-1] != 0:
				repl_exec( stmt[2][1], memory )
			else:
				repl_exec( stmt[3][1], memory )

		# ( 'PROC', name, params, body )
		elif stmt[0] == 'PROC':
			memory[ '%proc' ][ stmt[1] ] = stmt # more lazy
			# memory[ '%proc' ][ stmt[1][0] ] = ('FUNC',stmt[2],stmt[3])

		elif stmt[0] == 'PRINT':
			for param in stmt[1]:
				try:
					tmp = expand_expr( memory[ param ], memory )
					print( rpn_exec( tmp, memory ), end=' ' )
				except:
					print( "RUNTIME ERROR: print: variable <%s> not assigned" % (param,) )
					# exit()
			print()

def repl( ):
	memory = memory_model()
	while True:
		line = nextline( '>>> ', quit=True )
		#line = sys.stdin.readline()
		if not line: break
		# look for those dones to complete if/while statements
		if 'if' in line or 'while' in line or 'proc' in line:
			while not done_match( line ):
				tmp = nextline( '... ' )
				if tmp: line += tmp
				else: break

		program = Parser( list(line) ).run()

		# pprint( program )
		try:
			repl_exec( program, memory )
		except KeyboardInterrupt:
			print( "interrupt repl_exec" )

		#mprint( memory )
		#print( memory )

	# mprint( memory )

def nextline( msg, quit=False ):
	try:
		return input( msg ) + '\n'
	except KeyboardInterrupt:
		print( 'interrupt nextline' )
		return nextline( msg )
	except EOFError:
		if quit: exit()
		else: return

# batch everything

def mprint( memory ):
	items = sorted( memory.items() )

	'''
	print( 'Procedures:' )
	for key, val in items[0][1].items():
		print( '  ',key )
		print( '  params:',val[0] )
		pprint( val[1], 4 )
	'''

	print( 'Memory:' )
	print( items[1:] )

def memory_model():
	mem = {}
	mem[ '%proc' ] = { # more lazy 4 tuple for all stmt
		('read','ID') : ( 'MACRO',None,'READ',0 ),
		('sprint','ID') : ( 'MACRO',None,'SPRINT',0 ),
		('string','ID') : ( 'MACRO',None,'STRING',1 ),
		('fprint','ID') : ( 'MACRO',None,'FPRINT',0 )
	}
	mem[ '%macro' ] = {
		'READ' : read_input,
		'SPRINT' : sprint,
		'STRING' : string,
		'FPRINT' : fprint
	}
	return mem

# all macros take stack param
def read_input( stack, args ):
	global READ
	if not READ:
		READ=open( 'input' )
		READ.seek(0)

	try:
		# blocking ?
		stack.append( float( READ.readline() ) )
	except:
		print( 'RUNTIME ERROR: read: not enough input' )
		stack.append( 0.0 )
		# exit()

def sprint( stack, args ):
	# all function on stack are be resolved
	for c in stack:
		try:
			char = chr(int( c ))
			print( char, end='' )
		except:
			print( c, end='' )

def fprint( stack, args ):
	print( stack )

def string( stack, args ):
	keys = 'nu_'
	codes = {
		'n' : '\n',
		'u' : '_',
		'_' : ' '
	}
	letters = re.sub( r'_([%s])' % keys, lambda x: codes[x.groups(1)[0]], args[0][0] )
	for i in letters:
		stack.append( ord(i) )

def resolve( stack, args ):
	print( stack, args )

def done_match( line ):
	words = re.sub( r'\t|\n|;', ' ', line).split(' ') 
	count = collections.Counter( words )

	while count['if']:
		count['done'] -= 2
		count['if'] -= 1

	while count['while']:
		count['done'] -= 1
		count['while'] -= 1

	while count['proc']:
		count['done'] -= 1
		count['proc'] -= 1

	while count['\\']:
		count['done'] -= 1
		count['\\'] -= 1

	# print( sorted(count.items()) )

	for key, val in count.items():
		if val < 0:
			return False

	return True

if __name__ == '__main__':
	if len(sys.argv) == 1:
		REPL=True
		repl()
	elif sys.argv[1] == '-full':
		inp = ''
		for line in sys.stdin:
			inp += line

		program = Parser( list( inp ) ).run()
		repl_exec( program, memory_model() )

