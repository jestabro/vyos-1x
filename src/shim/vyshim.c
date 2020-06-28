#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <zmq.h>
#include "mkjson.h"

/*
 *
 *
 */

#ifdef DEBUG
#define DEBUG_ON 1
#else
#define DEBUG_ON 0
#endif
#define debug_print(fmt, ...) \
    do { if (DEBUG_ON) fprintf(stderr, fmt, ##__VA_ARGS__); } while (0)

#define SOCKET_PATH "ipc:///run/vyos-configd.sock"

#define GET_ACTIVE "cli-shell-api --show-active-only --show-show-defaults --show-ignore-edit showConfig"
#define GET_SESSION "cli-shell-api --show-working-only --show-show-defaults --show-ignore-edit showConfig"

#define COMMIT_MARKER "/var/tmp/initial_in_commit"

enum {
    SUCCESS =      1 << 0,
    ERROR_COMMIT = 1 << 1,
    ERROR_DAEMON = 1 << 2,
    PASS =         1 << 3
};


int initialization(void *);
int pass_through(char **, int);

int main(int argc, char* argv[])
{
    // string for node data: conf_mode script and tagnode, if applicable
    char string_node_data[256];
    string_node_data[0] = '\0';

    void *context = zmq_ctx_new();
    void *requester = zmq_socket(context, ZMQ_REQ);

    debug_print("Connecting to vyos-configd ...\n");
    zmq_connect(requester, SOCKET_PATH);

    if (access(COMMIT_MARKER, F_OK) != -1) {
        remove(COMMIT_MARKER);
        initialization(requester);
    }

    int end = argc > 3 ? 3 : argc - 1;

    for (int i = end; i > 0 ; i--) {
        strncat(&string_node_data[0], argv[i], 127);
    }

    char error_code[1];
    debug_print("Sending node data ...\n");
    char *string_node_data_msg = mkjson(MKJSON_OBJ, 2,
                                        MKJSON_STRING, "type", "node",
                                        MKJSON_STRING, "data", &string_node_data[0]);

    zmq_send(requester, string_node_data_msg, strlen(string_node_data_msg), 0);
    zmq_recv(requester, error_code, 1, 0);
    debug_print("Received node data receipt\n");

    int err = (int)error_code[0];

    free(string_node_data_msg);

    zmq_close(requester);
    zmq_ctx_destroy(context);

    if (err & PASS) {
        debug_print("Received PASS\n");
        int ret = pass_through(argv, end);
        return ret;
    }

    if (err & ERROR_COMMIT) {
        debug_print("Received ERROR_COMMIT\n");
        return -1;
    }

    if (err & ERROR_DAEMON) {
        debug_print("Received ERROR_DAEMON\n");
        return -1;
    }

    return 0;
}

int initialization(void* Requester)
{
    char *active_str = NULL;
    size_t active_len = 0;

    char *session_str = NULL;
    size_t session_len = 0;

    char buffer[16];

    debug_print("Sending init announcement\n");
    char *init_announce = mkjson(MKJSON_OBJ, 1,
                                 MKJSON_STRING, "type", "init");
    zmq_send(Requester, init_announce, strlen(init_announce), 0);
    zmq_recv(Requester, buffer, 16, 0);
    debug_print("Received init receipt\n");

    free(init_announce);

    FILE *fp_a = popen(GET_ACTIVE, "r");
    getdelim(&active_str, &active_len, '\0', fp_a);

    debug_print("Sending active config\n");
    zmq_send(Requester, active_str, active_len - 1, 0);
    zmq_recv(Requester, buffer, 16, 0);
    debug_print("Received active receipt\n");

    free(active_str);

    FILE *fp_s = popen(GET_SESSION, "r");
    getdelim(&session_str, &session_len, '\0', fp_s);

    debug_print("Sending session config\n");
    zmq_send(Requester, session_str, session_len - 1, 0);
    zmq_recv(Requester, buffer, 16, 0);
    debug_print("Received session receipt\n");

    free(session_str);

    pclose(fp_a);
    pclose(fp_s);

    return 0;
}

int pass_through(char **argv, int end)
{
    char *newargv[] = { NULL, NULL };
    pid_t child_pid;

    newargv[0] = argv[end];
    if (end > 1) {
        putenv(argv[end - 1]);
    }

    if ((child_pid=fork()) < 0) {
        debug_print("fork() failed\n");
        return -1;
    } else if (child_pid == 0) {
        if (-1 == execv(argv[end], newargv)) {
            debug_print("pass_through execve failed %s: %s\n",
                        argv[end], strerror(errno));
            return -1;
        }
    } else if (child_pid > 0) {
        int status;
        pid_t wait_pid = waitpid(child_pid, &status, 0);
         if (wait_pid < 0) {
             debug_print("waitpid() failed\n");
             return -1;
         } else if (wait_pid == child_pid) {
             if (WIFEXITED(status)) {
                 debug_print("child exited with code %d\n",
                             WEXITSTATUS(status));
             }
         }
    }

    return 0;
}

