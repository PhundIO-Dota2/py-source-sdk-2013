//=============================================================================//
// This file is automatically generated. CHANGES WILL BE LOST.
//=============================================================================//
#include "cbase.h"
#include "srcpy.h"

// memdbgon must be the last include file in a .cpp file!!!
#include "tier0/memdbgon.h"

using namespace boost::python;

// The init method is in one of the generated files declared
#ifdef _WIN32
extern "C" __declspec(dllexport) PyObject* PyInit_srcbuiltins();
extern "C" __declspec(dllexport) PyObject* PyInit__entities();
extern "C" __declspec(dllexport) PyObject* PyInit__entitiesmisc();
#else
extern "C"  PyObject* PyInit_srcbuiltins();
extern "C"  PyObject* PyInit__entities();
extern "C"  PyObject* PyInit__entitiesmisc();
#endif // _WIN32

// The append function
void AppendSharedModules()
{
	APPEND_MODULE(srcbuiltins)
	APPEND_MODULE(_entities)
	APPEND_MODULE(_entitiesmisc)
}
