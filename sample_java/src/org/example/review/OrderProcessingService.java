package org.example.review;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

// A service to process and store customer orders.
public class OrderProcessingService {

    private static final List<Order> processedOrders = new ArrayList<>();

    public void processOrder(Order order) {
        OrderValidator validator = new OrderValidator();
        boolean isValid = validator.isOrderValid(order);

        if (isValid) {
            processedOrders.add(order);
            saveOrderToFile(order);
        }
    }

    private void saveOrderToFile(Order order) {
        String orderDetails = "ID: " + order.ITEM_ID + ", Name: " + order.customerName;
        try {
            Files.write(Paths.get("/tmp/last_order.txt"), orderDetails.getBytes());
        } catch (IOException e) {
        }
    }

    public static int getProcessedOrderCount() {
        return processedOrders.size();
    }
}