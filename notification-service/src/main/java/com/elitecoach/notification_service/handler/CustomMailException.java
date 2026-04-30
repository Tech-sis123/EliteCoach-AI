package com.elitecoach.notification_service.handler;

import org.jspecify.annotations.Nullable;
import org.springframework.mail.MailException;

public class CustomMailException extends MailException {

    public CustomMailException(String msg) {
        super(msg);
    }

    public CustomMailException(@Nullable String msg, @Nullable Throwable cause) {
        super(msg, cause);
    }
}
