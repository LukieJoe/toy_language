from lexer import Lexer
import sys
import traceback

# [ "LP","RP","MUL","DIV","ADD","SUB","EXP","ASN","SEP" ] [ "BAND","BOR","MOD","GT","LT","NOT" ]

_expr_types = [ "LP","RP","MUL","DIV","ADD","SUB","EXP","NEG","FUNC","RFUNC","BAND","BOR","MOD","GT","LT","NOT","ID","LITERAL" ]
_emdas = ["ID","FUNC","RFUNC","NEG","EXP","MUL","DIV","ADD","SUB" ] + [ "BAND","BOR","MOD","GT","LT","NOT" ]

class Parser():
	def __init__(self, input_list):
		self.lexer = Lexer( input_list )

	def run(self):
		return self.stmts()

	def stmts(self):
		if not self.lexer.peek_token() or self.lexer.peek_token()[1] == 'DONE':
			return []

		return [self.stmt()] + self.stmts()

	def stmt(self):
		peek = self.lexer.peek_token()
		if peek and peek[1] == "IF":
			return self.cond()

		if peek and peek[1] == "WHILE":
			return self.loop()

		if peek and peek[1] == "PROC":
			return self.proc()

		if peek and peek[1] == "PRINT":
			return self.print()

		if peek and peek[1] == "RET":
			return self.ret()

		peek = self.lexer.peek_token(depth=2)
		if peek and peek[1] == "ASN":
			return self.asn()

		expr = self.expr()
		self.match_token( ["SEP"] )
		return expr

	def asn(self):
		iden = self.match_token("ID")[0]
		self.match_token( ["ASN"] )
		expr = self.expr()
		self.match_token( ["SEP"] )
		return ( 'ASSIGNMENT',iden,expr )

	def _nieve_expr(self):
		peek = self.lexer.peek_token()
		if peek and peek[1] == "SEP":
			return []

		return [self.match_token( _expr_types )] + self.nieve_expr()

	def nieve_expr(self):
		return ( 'EXPR', _nieve_expr )

	# shunting_yard
	def expr(self):
		rpn = []
		stack = []

		while True:
			peek = self.lexer.peek_token()
			if not peek or peek[1] == 'SEP':
				break

			if peek[1] in ['FUNC','RFUNC']:
				token = self.func()
			else:
				token = self.match_token( _expr_types )

			# [ 'LITERAL', 'ID' ] for variables
			if token[1] in ["LITERAL"]:
				rpn.append(token)
			elif token[1] in _emdas:
				while stack:
					if stack[-1][1] == "LP": break
					elif _emdas.index(stack[-1][1]) <= _emdas.index(token[1]):
						rpn.append(stack.pop())
					else: break
				stack.append(token)
			elif token[1] in ["LP"]:
				stack.append(token)
			elif token[1] in ["RP"]:
				top = stack[-1]
				while top[1] != "LP":
					rpn.append(stack.pop())
					top = stack[-1]

				stack.pop()

		while stack:
			if not stack[-1][1] in _emdas + ['LP']:
				break
			rpn.append(stack.pop())

		if stack:
			print( "ERROR: invalid expr, unparsed values", stack )
			exit()

		return ( 'EXPR',rpn )

	def func(self):
		func = self.match_token( ['FUNC','RFUNC'] )[1]
		params = self.params()
		self.match_token( ['SEP'] )
		stmts = self.stmts()
		self.match_token( ['DONE'] )
		self.match_token( ['SEP'] )

		# token[1] == FUNC
		# token[2] == [params]
		# token[3] == [stmts]

		return ('FUNC',func,params,stmts)

	def match_token(self, t):
		token = self.lexer.next_token()

		if token and token[1] in t:
			return token 
		else:
			last = self.lexer.output
			print( "ERROR: invalid syntax <",token,"> is not of type", t )

			if last:
				print( "-- last valid tokens:\n ", end='' )
				for tok, _ in last: print( tok, end=' ' )
				print()
			else:
				traceback.print_stack()

			exit()

	# if expr sep stmts done else stmts done
	def cond(self):
		self.match_token( ['IF'] )
		expr = self.expr()
		self.match_token( ['SEP'] )
		_if = self.stmts()
		self.match_token( ['DONE'] )
		self.ignore_sep()
		self.match_token( ['ELSE'] )
		_else = self.stmts()
		self.match_token( ['DONE'] )
		self.match_token( ['SEP'] )	
		return ( 'BRANCH', expr, ('IF-BODY',_if), ('ELSE-BODY',_else) )

	def ignore_sep(self):
		peek = self.lexer.peek_token()
		while peek and peek[1] == "SEP":
			self.match_token( ['SEP'] )
			peek = self.lexer.peek_token()

	# while expr sep stmts done
	def loop(self):
		self.match_token( ['WHILE'] )
		expr = self.expr()
		self.match_token( ['SEP'] )
		body = self.stmts()
		self.match_token( ['DONE'] )
		self.match_token( ['SEP'] )	
		return ( 'LOOP', expr, ('LOOP-BODY',body) )

	def proc(self):
		self.match_token( ['PROC'] )
		name = self.match_token( ['ID'] )
		params = self.params()
		self.match_token( ['SEP'] )
		body = self.stmts()
		self.match_token( ['DONE'] )
		self.match_token( ['SEP'] )	
		return ( 'PROC', name, params, body )

	def params(self):
		peek = self.lexer.peek_token()
		if not peek or peek[1] == 'SEP':
			return []

		return [self.match_token( ['ID'] )] + self.params()

	def print(self):
		self.match_token( ['PRINT'] )
		params = self.params()
		return ( 'PRINT',params )

	def ret(self):
		self.match_token( ['RET'] )
		expr = self.expr()
		self.match_token( ['SEP'] )
		return ( 'ASSIGNMENT','%ret',expr )

def pprint( program, indent=0 ):
	p = " "*indent
	for stmt in program:
		print( p,' STMT' )
		if stmt[0] == 'ASSIGNMENT':
			print( p,'  ',stmt[0] )    # assignment
			print( p,'    ',stmt[1] ) # ID
			print( p,'    ',stmt[2][0] ) # expr
			print( p,'      ',stmt[2][1] ) 

		elif stmt[0] == 'EXPR':
			print( p,'  ',stmt[0] ) # expr
			print( p,'    ',stmt[1] )

		elif stmt[0] == 'LOOP':
			print( p,'  ',stmt[0] ) # loop
			print( p,'    ',stmt[1][0] ) # expr
			print( p,'      ',stmt[1][1] ) # expr list
			print( p,'    ',stmt[2][0] ) # stmts
			pprint( stmt[2][1], indent=indent+6 )

		elif stmt[0] == 'BRANCH':
			print( p,'  ',stmt[0] ) # branch
			print( p,'    ',stmt[1][0] ) # expr
			print( p,'      ',stmt[1][1] ) # expr list
			print( p,'    ',stmt[2][0] ) # if-body
			pprint( stmt[2][1], indent=indent+6 ) # stmts
			print( p,'    ',stmt[3][0] ) # else-body
			pprint( stmt[3][1], indent=indent+6 ) # stmts

		elif stmt[0] in ['PROC','FUNC']:
			print( p,'  ',stmt[0] ) # proc
			print( p,'    ',stmt[1] ) # label
			print( p,'    ',stmt[2] ) # params
			print( p,'    ',stmt[3] ) # body

		elif stmt[0] == 'PRINT':
			print( p,'  ',stmt[0] )
			print( p,'    ',stmt[1] )

if __name__ == '__main__':
	program = ''
	for line in sys.stdin:
		program = program + line

	out = Parser( list(program) ).run()
	pprint( out )
