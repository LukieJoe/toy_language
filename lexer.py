import sys

# Comparison lists
_operator = [  "(", ")",  "*",  "/",  "+",  "-",  "^",  "=",  "\\",    "$",   "&",  "|",  "%", ">", "<",  "!",    ":" ]
_op_types = [ "LP","RP","MUL","DIV","ADD","SUB","EXP","ASN","FUNC","RFUNC","BAND","BOR","MOD","GT","LT","NOT", ":ASN" ]
_operator_tuple = list( zip(_operator,_op_types) )

_skip = [ "\t", " " ]
_separator = [ "\n", ";" ] 
_alpha = [ chr(i) for i in range(65,123) if not i in range(91,97) ] + ['_'] 
_numeric = [ str(i) for i in range(10) ] + ['.']

_unary = ['-']
_unary_tuple = [('~','NEG')]

_keywords = ['if','else','while','done','proc','print','ret']

# Valid States
END=-1
START=0
IDENTIFIER=1
LITERAL=2
SEPARATOR=3
OPERATOR=4

# run() returns the next state given input[0]
class State:
	def run(self,input_list,output):
		raise NotImplementedError

# empty
class Identifier(State):

	def __init__(self):
		self.token = []

	def check_return(self, output_list):
		tok = "".join( self.token )
		if tok in _keywords:
			output_list.append( (tok,tok.upper()) )
		else:
			output_list.append( (tok,"ID") )
		self.token.clear()

	def run( self, input_list, output_list ):

		if not input_list:
			self.check_return(output_list)
			return END

		elif input_list[0] in _alpha + _numeric:
			self.token.append( input_list[0] )
			input_list.pop(0)
			return IDENTIFIER

		elif input_list[0] in _skip:
			self.check_return(output_list)
			input_list.pop(0)
			return START

		elif input_list[0] in _separator:
			self.check_return(output_list)
			return SEPARATOR

		elif input_list[0] in _operator:
			self.check_return(output_list)
			return OPERATOR

		else:
			self.check_return(output_list)
			return END

# give, limited
class Literal(State):

	def __init__(self):
		self.token = []

	def run( self, input_list, output_list ):

		if not input_list:
			output_list.append( ("".join( self.token ),"LITERAL") )
			self.token.clear()
			return END

		elif input_list[0] in _skip:
			output_list.append( ("".join( self.token ),"LITERAL") )
			self.token.clear()
			input_list.pop(0)
			return START

		elif input_list[0] in _separator:
			output_list.append( ("".join( self.token ),"LITERAL") )
			self.token.clear()
			return SEPARATOR

		elif input_list[0] in _operator:
			output_list.append( ("".join( self.token ),"LITERAL") )
			self.token.clear()
			return OPERATOR

		elif input_list[0] in _alpha:
			output_list.append( ("".join( self.token ),"LITERAL") )
			self.token.clear()
			return IDENTIFIER

		elif input_list[0] in _numeric:
			self.token.append( input_list[0] )
			input_list.pop(0) 
			return LITERAL

		else:
			output_list.append( ("".join( self.token ),"LITERAL") )
			self.token.clear()
			return END

# empty
class Start(State):

	def run( self, input_list, output_list ):

		if not input_list:
			return END

		elif input_list[0] in _skip:
			input_list.pop(0)
			return START

		elif input_list[0] in _separator:
			return SEPARATOR

		elif input_list[0] in _operator:
			return OPERATOR

		elif input_list[0] in _numeric:
			return LITERAL

		elif input_list[0] in _alpha:
			return IDENTIFIER

		else:
			return END 

# empty
class Separator(State):
	def run( self, input_list, output_list ):

		if input_list and input_list[0] in _separator:
			output_list.append( (input_list[0],"SEP") )
			input_list.pop(0)
			return START

		else:
			return END
# empty
class Operator(State):
	def run( self, input_list, output_list):

		# unary NEG
		if len( input_list ) > 1 and input_list[0] in _unary \
			and input_list[1] in _alpha+_numeric+['(']:

			if not output_list or output_list[-1] in _operator_tuple:
				i = _unary.index( input_list[0] )
				output_list.append( _unary_tuple[i] )
				input_list.pop(0)
				return START

		if input_list and input_list[0] in _operator:
			i = _operator.index( input_list[0] )
			output_list.append( _operator_tuple[i] )
			input_list.pop(0)
			return START

		else:
			return END

class Lexer():
	machine = {
		START : Start(),
		IDENTIFIER : Identifier(),
		LITERAL : Literal(),
		SEPARATOR : Separator(),
		OPERATOR : Operator()
	}

	def __init__(self, input_list):
		self.state = START
		self.input = input_list.copy()
		self.output = []

	def next_token(self):
		old = self.output.copy()

		while old == self.output and self.state != END:
			self.state = self.machine[ self.state ].run( self.input, self.output )

		if old != self.output:
			return self.output[-1]

	def peek_token(self, depth=1):
		old = self.output.copy()
		new = self.output.copy()
		inp = self.input.copy()
		state = self.state

		while len(new)-len(old) != depth and state != END:
			state = self.machine[ state ].run( inp, new )

		if old != new:
			return new[-1]

	def all_tokens(self):
		while self.state != END:
			self.state = self.machine[ self.state ].run( self.input, self.output )
		return self.output

if __name__ == "__main__":
	# Gather the inputstring from stdin
	instr = ""
	for line in sys.stdin:
		instr = instr + line

	# convert the string into a list of characters
	input_list = list( instr )

	lexer = Lexer( input_list )
	output = lexer.all_tokens()

	if lexer.input:
		print( "ERROR: invalid symbol [ %s ]" % lexer.input[0] )
	else:
		print( output )

