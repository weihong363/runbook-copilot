package com.ironion.mock;

import org.slf4j.MDC;

/**
 * 日志上下文工具类
 * 用于管理 MDC（Mapped Diagnostic Context）中的追踪信息
 */
public class LogContext {
    
    private static final String TRACE_ID_KEY = "traceId";
    private static final String SPAN_ID_KEY = "spanId";
    
    /**
     * 设置追踪上下文
     * @param traceId 追踪ID
     * @param spanId 跨度ID
     */
    public static void setContext(String traceId, String spanId) {
        MDC.put(TRACE_ID_KEY, traceId);
        MDC.put(SPAN_ID_KEY, spanId);
    }
    
    /**
     * 清除追踪上下文
     */
    public static void clearContext() {
        MDC.clear();
    }
}
