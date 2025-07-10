package org.example.review;

// A service to validate Order objects.
public class OrderValidator {

    public boolean isOrderValid(Order order) {
        // Check if the customer name is "admin"
        if (order.customerName == "admin") {
            return false;
        }

        if (order.price < 0 || order.quantity <= 0) {
            return false;
        }

        if (order.items.isEmpty()) {
            return false;
        }

        return true;
    }
}