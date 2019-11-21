from __future__ import print_function
from pprint import pprint

from org.objectweb.asm import ClassReader, ClassVisitor, MethodVisitor, Type
from org.objectweb.asm.Opcodes import ASM7, ACC_STATIC, ACC_PUBLIC


well_known = {
    Type.VOID_TYPE: "None",
    
    Type.BOOLEAN_TYPE: "bool",

    Type.CHAR_TYPE: "int",
    Type.SHORT_TYPE: "int",
    Type.INT_TYPE: "int",
    Type.LONG_TYPE: "int",

    Type.FLOAT_TYPE: "float",
    Type.DOUBLE_TYPE: "float",

    Type.getType("Ljava/lang/Object;"): "Any",
    Type.getType("Ljava/lang/String;"): "str",

    # FIXME: add generic support
    Type.getType("Ljava/util/Collection;"): "Collection",
    Type.getType("Ljava/util/List;"): "List",
    Type.getType("Ljava/util/Map;"): "Map",
    Type.getType("Ljava/util/Set;"): "Set",
    Type.getType("Ljava/util/Iterator;"): "Iterator",
    Type.getType("Ljava/util/Iterable;"): "Iterable",

    # FIXME: add arg types
    Type.getType("Ljava/util/function/Function;"): "Callable",
    Type.getType("Ljava/util/function/BiFunction;"): "Callable",
    Type.getType("Ljava/util/function/BiConsumer;"): "Callable",
}


def to_classname(java_type, path=True):
    classname = str(java_type).replace("/", ".")
    if not path:
        return classname.split(".")[-1]
    else:
        return classname
    

def to_typename(java_type):
    str_java_type = str(java_type)
    is_list = False
    if str_java_type[0] == "[":
        is_list = True
        java_type = Type.getType(str_java_type[1:])
    typename = well_known.get(java_type)
    if typename is None:
        typename = (str(java_type)).replace("/", ".")[1: -1]
    if is_list:
        return "List[%s]" % (typename,)
    else:
        return typename
        

class MethodStub(MethodVisitor):
    def __init__(self, access, name, desc, signature):
        self.is_static = access & ACC_STATIC
        self.is_public = access & ACC_PUBLIC
        self.name = name
        method_type = Type.getMethodType(desc)
        self.param_types = method_type.getArgumentTypes()
        self.return_type = method_type.getReturnType()
        self.signature = signature
        if self.is_static:
            # FIXME - this should be different, but need to dig deeper!
            self.params = [None] * (len(self.param_types) + 1)
        else:
            self.params = [None] * (len(self.param_types) + 1)
        super(MethodVisitor, self).__init__(ASM7)

    def visitLocalVariable(self, name, desc, signature, start, end, index):
        # Calling convention in Java is to pass the following as local variables:
        # 0: this
        # 1..num_params+1: param
        #
        # See this code for an example
        # https://github.com/airlift/parameternames/blob/master/src/main/java/io/airlift/parameternames/ParameterNames.java
        
        if index <= len(self.param_types):
            self.params[index] = (name, Type.getType(desc), signature)

    # FIXME: need to union methods with same names (constructor/method
    # overloading), as especially seen in __init__/<init>
    def visitEnd(self):
        if self.is_static:
            return
        if not self.is_public:
            return

        if self.name == "<init>":
            name = "__init__"
        else:
            name = self.name

        display_params = []
        if self.is_static:
            params = self.params
        else:
            display_params.append("self")
            params = self.params[1:]
            
        for param in params:
            try:
                display_params.append("%s: %s" % (param[0], to_typename(param[1])))
            except:
                pass

        if self.is_static:
            print("@staticmethod")
        print("  def %s(%s) -> %s: ..." % (
            name, ", ".join(display_params), to_typename(self.return_type)))


class ClassStub(ClassVisitor):

    def __init__(self):
        super(ClassVisitor, self).__init__(ASM7)
    
    def visit(self, version, access, name, signature, superName, interfaces):
        bases = [superName]
        if interfaces:
            bases.extend(interfaces)
        print("class %s(%s):" % (
            to_classname(name, path=False),
            ", ".join(to_classname(base) for base in bases)))

    def visitMethod(self, access, name, desc, signature, exceptions):
        return MethodStub(access, name, desc, signature)


def make_stub_for_class(classname):
    cp = ClassStub()
    cr = ClassReader(classname)
    cr.accept(cp, 0)


if __name__ == "__main__":
    import sys
    
    make_stub_for_class(sys.argv[1])
