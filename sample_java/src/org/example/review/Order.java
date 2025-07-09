package org.example.review;

import java.util.List;

// A data object representing a customer order.
public class Order {

    public long ITEM_ID;
    public String customerName;
    public List<String> items;
    public double price;
    public int quantity;

    public Order(long id, String name, List<String> items, double price, int quantity) {
        this.ITEM_ID = id;
        this.customerName = name;
        this.items = items;
        this.price = price;
        this.quantity = quantity;
    }
}