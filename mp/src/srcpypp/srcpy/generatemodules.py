import sys
import os
import re

from . import genvpc
from . import vpcutil

def RegisterModules(settings):
    ''' Finds and creates the lists of modules to be parsed. '''
    registered_modules = []
    for am in settings.modules:
        mod = __import__(am[0])
        moduleinst = getattr(mod, am[1])()
        moduleinst.settings = settings
        registered_modules.append(moduleinst)
    return registered_modules
#
# Append code generation
#        
appendtemplate = '''//=============================================================================//
// This file is automatically generated. CHANGES WILL BE LOST.
//=============================================================================//
#include "cbase.h"
#include "srcpy.h"

// memdbgon must be the last include file in a .cpp file!!!
#include "tier0/memdbgon.h"

using namespace boost::python;

// The init method is in one of the generated files declared
#ifdef _WIN32
%(win32decls)s
#else
%(unixdecls)s
#endif // _WIN32

// The append function
void Append%(AppendFunctionName)sModules()
{
%(appendlist)s
}
'''

def GenerateAppendCode(modulenames, dllname):
    win32decls = []
    unixdecls = []
    appendlist = []
    for name in modulenames:
        # PYINIT macro either evaluates to PyInit_ (py3) or init_ (py2)
        win32decls.append('extern "C" __declspec(dllexport) PYINIT_DECL(%s)();' % (name))
        unixdecls.append('extern "C" PYINIT_DECL(%s)();' % (name))
        appendlist.append('\tAPPEND_MODULE(%s)' % (name))
        
    return appendtemplate % {
        'win32decls' : '\n'.join(win32decls),
        'unixdecls' : '\n'.join(unixdecls),
        'appendlist' : '\n'.join(appendlist),
        'AppendFunctionName' : dllname[0].capitalize() + dllname[1:len(dllname)],
    }

def GenerateAppendFile(path, module_names, dll_name):
    ''' Writes the append file, which registers all modules in Python.'''
    filename = 'src_append_%s.cpp' % (dll_name)
    path = os.path.join(path, filename)
    
    appendcode = GenerateAppendCode(module_names, dll_name)
    if os.path.exists(path):
        try:
            with open(path, 'r') as fp:
                oldappendcode = fp.read()
            if oldappendcode == appendcode:
                return path # Unchanged
        except IOError as e:
            print('Could not read "%s": %s' % (path, e))
    
    print('Writing append file "%s" (changed)' % (path))
    with open(path, 'w+') as fp:
        fp.write(appendcode)
    return path
        
def GetFilenames(rm, isclient=False):
    rm.isclient = isclient
    rm.isserver = not isclient
    
    os.chdir(rm.vpcdir)
    
    path = os.path.relpath(rm.path, rm.srcdir)
    if not rm.split:
        return [os.path.join(path, '%s.cpp' % (rm.module_name))]
    else:
        files = os.listdir(os.path.join(rm.path, rm.module_name))
        files = filter(lambda f: f.endswith('.cpp') or f.endswith('.hpp'), files)
        return map(lambda f: os.path.join(path, rm.module_name, f), files)

def ParseModules(settings, specificmodule=None, appendfileonly=False):
    ''' Main parse function.
    
        Args:
            settings (module): Module containing settings for this configuration.
            specificmodule (str): Parse a single specific module.
            appendfileonly (bool): Only generate the append file.
    '''
    # Keep a list of the append names
    client_modules = []
    server_modules = []
    shared_modules = []
    
    # Keep a list of the filenames
    client_filenames = []
    server_filenames = []
    shared_filenames = []
    
    # Add search paths and create list of modules to be parsed/exposed
    srcpath = settings.srcpath
    for path in settings.searchpaths:
        sys.path.append(os.path.join(srcpath, path))
    
    moduleinstances = RegisterModules(settings)
    
    # Parse vpc files
    macros = {
        'GAMENAME' : 'pysource', 
        'OUTDLLEXT' : '.so', 
        '_DLL_EXT' : '.so', 
        'PLATFORM' : 'POSIX=1',
        
        # Conditions
        'POSIX' : '',
        'LINUX' : '',
        'LINUXALL' : '',
        'SOURCESDK' : '', # Operate in Source SDK context (TODO: parse from default.vgc?)
    }
    
    vpcserverpath = os.path.abspath(settings.vpcserverpath)
    vpcclientpath = os.path.abspath(settings.vpcclientpath)
    
    srcpyppdir = os.getcwd()
    servervpcdir = os.path.dirname(vpcserverpath)
    clientvpcdir = os.path.dirname(vpcclientpath)
    
    os.chdir(servervpcdir)
    servervpc = vpcutil.ParseVPC(vpcserverpath, macros=dict(macros))
    vpcutil.ApplyMacrosToNodes(servervpc, servervpc.macros)
    serverincludes = vpcutil.NormIncludeDirectories(servervpc['$Configuration']['$Compiler']['$AdditionalIncludeDirectories'].nodevalue)
    serverincludes = list(filter(os.path.exists, re.findall('[^;,]+', serverincludes)))
    serversymbols = servervpc['$Configuration']['$Compiler']['$PreprocessorDefinitions'].nodevalue
    serversymbols = list(filter(bool, serversymbols.split(';')))
    
    os.chdir(clientvpcdir)
    clientvpc = vpcutil.ParseVPC(vpcclientpath, macros=dict(macros))
    vpcutil.ApplyMacrosToNodes(clientvpc, clientvpc.macros)
    clientincludes = vpcutil.NormIncludeDirectories(servervpc['$Configuration']['$Compiler']['$AdditionalIncludeDirectories'].nodevalue)
    clientincludes = list(filter(os.path.exists, re.findall('[^;,]*', clientincludes)))
    clientsymbols = clientvpc['$Configuration']['$Compiler']['$PreprocessorDefinitions'].nodevalue
    clientsymbols = list(filter(bool, clientsymbols.split(';')))
    
    os.chdir(srcpyppdir)
    
    for rm in moduleinstances:
        assert rm.module_name, 'Modules must have a valid name'
        
        rm.servervpcdir = servervpcdir
        rm.clientvpcdir = clientvpcdir
        rm.serverincludes = serverincludes
        rm.clientincludes = clientincludes
        rm.serversymbols = serversymbols
        rm.clientsymbols = clientsymbols
        rm.serversrcdir = servervpc.macros['SRCDIR']
        rm.clientsrcdir = clientvpc.macros['SRCDIR']
        
        # Check if we should parse this module
        if not appendfileonly and (not specificmodule or specificmodule == rm.module_name):
            # Generate binding code
            print('Generating %s...' % (rm.module_name))
            rs = rm.Run()
    
        # Build module list for append code
        if rm.module_type == 'client':
            client_modules.append(rm.module_name)
            client_filenames.extend(GetFilenames(rm))
        elif rm.module_type == 'server':
            server_modules.append(rm.module_name)
            server_filenames.extend(GetFilenames(rm))
        else:
            shared_modules.append(rm.module_name)
            if rm.split:
                client_filenames.extend(GetFilenames(rm, isclient=True))
                server_filenames.extend(GetFilenames(rm, isclient=False))
            else:
                shared_filenames.extend(GetFilenames(rm))
                
     # Change back to srcpypp directory
    os.chdir(srcpyppdir)

    # Generate new append files if needed (add modules to Python on initialization)
    srcpath = settings.srcpath
    clientappendfile = GenerateAppendFile(os.path.join(srcpath, settings.client_path), client_modules, 'client')
    serverappendfile = GenerateAppendFile(os.path.join(srcpath, settings.server_path), server_modules, 'server')
    sharedappendfile = GenerateAppendFile(os.path.join(srcpath, settings.shared_path), shared_modules, 'shared')
    
    # Add append files for autoupdatevxproj setting if specified
    if client_filenames: 
        client_filenames.append(clientappendfile.split(rm.settings.srcpath)[1][1:])
    if server_filenames: 
        server_filenames.append(serverappendfile.split(rm.settings.srcpath)[1][1:])
    if shared_filenames: 
        shared_filenames.append(sharedappendfile.split(rm.settings.srcpath)[1][1:])
    
    # Generate VPC file with autogenerated file includes
    if hasattr(settings, 'vpcserverautopath'):
        genvpc.GenerateVPCs(settings, shared_filenames + server_filenames, settings.vpcserverautopath)
    if hasattr(settings, 'vpcclientautopath'):
        genvpc.GenerateVPCs(settings, shared_filenames + client_filenames, settings.vpcclientautopath)
        