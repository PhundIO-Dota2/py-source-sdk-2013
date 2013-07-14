// This file has been generated by Py++.

#include "cbase.h"
// This file has been generated by Py++.

#include "boost/python.hpp"
#include "cbase.h"
#include "SkyCamera.h"
#include "ai_basenpc.h"
#include "srcpy_entities.h"
#include "srcpy.h"
#include "tier0/memdbgon.h"
#include "_entities_free_functions_pypp.hpp"

namespace bp = boost::python;

void register_free_functions(){

    { //::CreateEntityByName
    
        typedef ::CBaseEntity * ( *CreateEntityByName_function_type )( char const *,int );
        
        bp::def( 
            "CreateEntityByName"
            , CreateEntityByName_function_type( &::CreateEntityByName )
            , ( bp::arg("className"), bp::arg("iForceEdictIndex")=(int)(-0x000000001) )
            , bp::return_value_policy< bp::return_by_value >() );
    
    }

    { //::DispatchSpawn
    
        typedef int ( *DispatchSpawn_function_type )( ::CBaseEntity * );
        
        bp::def( 
            "DispatchSpawn"
            , DispatchSpawn_function_type( &::DispatchSpawn )
            , ( bp::arg("pEntity") ) );
    
    }

}

