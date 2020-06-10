#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <zmq.h>

/*
 * There is at least one unsafe practice here, but poc wip.
 *
 */

#define SOCKET_PATH "ipc:///run/vyos-configd.sock"

#define GET_ACTIVE "cli-shell-api --show-active-only --show-show-defaults --show-ignore-edit showConfig"

#define GET_SESSION "cli-shell-api --show-working-only --show-show-defaults --show-ignore-edit showConfig"

#define COMMIT_MARKER "/var/tmp/initial_in_commit"

int initialization(void *);

int main(int argc, char* argv[])
{
    // string for node data: conf_mode script and tagnode, if applicable
    char string_node_data[256];
    string_node_data[0] = '\0';

    void *context = zmq_ctx_new();
    void *requester = zmq_socket(context, ZMQ_REQ);

    printf("Connecting to vyos-configd ...\n");
    zmq_connect(requester, SOCKET_PATH);

    if (access(COMMIT_MARKER, F_OK) != -1) {
        remove(COMMIT_MARKER);
        initialization(requester);
    }

    int len = argc > 3 ? 3 : argc - 1;

    for (int i = len; i > 0 ; i--) {
        strncat(&string_node_data[0], argv[i], 127);
    }

    char buffer[16];
    printf("Sending node data ...\n");
    zmq_send(requester, string_node_data, strlen(string_node_data), 0);
    zmq_recv(requester, buffer, 16, 0);
    printf("Received\n");

    zmq_close(requester);
    zmq_ctx_destroy(context);
    return 0;
}

int initialization(void* Requester)
{
    char *active_str = NULL;
    size_t active_len = 0;

    char *session_str = NULL;
    size_t session_len = 0;

    char buffer[16];

    printf("Sending init announcement\n");
    zmq_send(Requester, "init", 4, 0);
    zmq_recv(Requester, buffer, 16, 0);
    printf("Received init\n");

    FILE *fp_a = popen(GET_ACTIVE, "r");
    getdelim(&active_str, &active_len, '\0', fp_a);

    printf("Sending active config\n");
    zmq_send(Requester, active_str, active_len - 1, 0);
    zmq_recv(Requester, buffer, 16, 0);
    printf("Received active receipt\n");

    free(active_str);

    FILE *fp_s = popen(GET_SESSION, "r");
    getdelim(&session_str, &session_len, '\0', fp_s);

    printf("Sending session config\n");
    zmq_send(Requester, session_str, session_len - 1, 0);
    zmq_recv(Requester, buffer, 16, 0);
    printf("Received session receipt\n");

    free(session_str);

    pclose(fp_a);
    pclose(fp_s);

    return 0;
}

