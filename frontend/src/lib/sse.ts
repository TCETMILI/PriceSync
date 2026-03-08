export const listenToPipelineStatus = (onMessage: (data: any) => void, onError: () => void) => {
    // SSE Stream endpoint
    const eventSource = new EventSource('http://localhost:8000/stream-status');

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            onMessage(data);
        } catch (err) {
            console.error("SSE Parse hatası", err);
        }
    };

    eventSource.onerror = () => {
        console.error("SSE Bağlantısı Koptu.");
        eventSource.close();
        onError();
    };

    return eventSource;
};

