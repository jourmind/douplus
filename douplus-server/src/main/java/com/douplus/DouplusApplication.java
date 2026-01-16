package com.douplus;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * DOU+投放管理系统启动类
 */
@SpringBootApplication
@MapperScan("com.douplus.*.mapper")
@EnableScheduling
@EnableAsync
public class DouplusApplication {
    public static void main(String[] args) {
        SpringApplication.run(DouplusApplication.class, args);
    }
}
