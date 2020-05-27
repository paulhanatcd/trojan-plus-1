#ifndef _PIPELINE_COMPONENT_H
#define _PIPELINE_COMPONENT_H

#include <stdint.h>
#include <set>
#include <stdexcept>

#include "core/utils.h"

class Config;
class Service;
class PipelineComponent{

public:
    typedef uint16_t SessionIdType;
    
private:

    // session id counter for pipeline mode
    static SessionIdType s_session_id_counter;
    static std::set<SessionIdType>  s_session_used_ids;

    Service* m_service;
    SessionIdType m_session_id;    
    bool m_is_use_pipeline;
    bool m_is_udp;
public:
    PipelineComponent(Service* _service, const Config& _config);
    
    int pipeline_ack_counter;
    bool pipeline_wait_for_ack;
    bool pipeline_first_call_ack;

    ReadDataCache pipeline_data_cache;
    void pipeline_in_recv(std::string &&data);

    void allocate_session_id();
    void free_session_id();
    inline SessionIdType get_session_id() const { return m_session_id; }
    void set_session_id(SessionIdType _id) { m_session_id = _id; }
    
    inline void set_use_pipeline() { m_is_use_pipeline = true; };
    inline bool is_using_pipeline(){ return m_is_use_pipeline; }
    inline void recv_ack_cmd() { pipeline_ack_counter++; }

    inline bool is_wait_for_pipeline_ack()const { return pipeline_wait_for_ack; }    

    inline bool pre_call_ack_func(){
        if(!pipeline_first_call_ack){
            if(pipeline_ack_counter <= 0){
                pipeline_wait_for_ack = true;
                return false;
            }
            pipeline_ack_counter--;
        }
        pipeline_wait_for_ack = false;
        pipeline_first_call_ack = false;
        return true;
    }
};

#endif //_PIPELINE_COMPONENT_H