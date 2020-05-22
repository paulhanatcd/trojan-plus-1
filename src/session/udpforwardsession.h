/*
 * This file is part of the trojan project.
 * Trojan is an unidentifiable mechanism that helps you bypass GFW.
 * Copyright (C) 2017-2020  The Trojan Authors.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _UDPFORWARDSESSION_H_
#define _UDPFORWARDSESSION_H_

#include <boost/asio/ssl.hpp>
#include <boost/asio/steady_timer.hpp>

#include "core/pipeline.h"
#include "socketsession.h"

class UDPForwardSession : public SocketSession {
public:
    typedef std::function<void(const boost::asio::ip::udp::endpoint&, const std::string&)> UDPWrite;
private:
    enum Status {
        CONNECT,
        FORWARD,
        FORWARDING,
        DESTROY
    } status;
    UDPWrite in_write;
    boost::asio::ssl::stream<boost::asio::ip::tcp::socket>out_socket;
    boost::asio::steady_timer gc_timer;
    std::pair<std::string, uint16_t> udp_target;
    boost::asio::ip::udp::socket udp_target_socket;
    boost::asio::ip::udp::endpoint udp_target_endpoint;

    Pipeline::ReadDataCache pipeline_data_cache;

    void out_recv(const std::string &data);
    void in_recv(const std::string &data);
    void out_async_read();
    void out_async_write(const std::string &data);
    
    void out_sent();
    void timer_async_wait();
public:
    UDPForwardSession(const Config &config, boost::asio::io_context &io_context, boost::asio::ssl::context &ssl_context, 
        const boost::asio::ip::udp::endpoint &endpoint, const std::pair<std::string, uint16_t>& targetdst, UDPWrite in_write);
    ~UDPForwardSession();
    
    boost::asio::ip::tcp::socket& accept_socket() override;
    void start() override;
    void start_udp(const std::string& data);
    void destroy(bool pipeline_call = false) override;
    bool process(const boost::asio::ip::udp::endpoint &endpoint, const std::string &data);
    
    void pipeline_out_recv(std::string &&data);
};

#endif // _UDPFORWARDSESSION_H_
