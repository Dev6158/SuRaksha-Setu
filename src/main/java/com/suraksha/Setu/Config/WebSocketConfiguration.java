package com.suraksha.Setu.Config;

import com.suraksha.Setu.Websocket.TelemetryWebSocketHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfiguration implements WebSocketConfigurer {

    private final TelemetryWebSocketHandler telemetryWebSocketHandler;

    public WebSocketConfiguration(TelemetryWebSocketHandler telemetryWebSocketHandler) {
        this.telemetryWebSocketHandler = telemetryWebSocketHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(telemetryWebSocketHandler, "/api/v1/telemetry/stream")
                .setAllowedOrigins("*");
    }
}
