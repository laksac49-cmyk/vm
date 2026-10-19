<?php
// Start output buffering to prevent stray output
ob_start();

// Disable error display to prevent HTML output
ini_set('display_errors', 0);
ini_set('display_startup_errors', 0);
error_reporting(E_ALL);

// Log errors to file for debugging
ini_set('log_errors', 1);
ini_set('error_log', 'C:/xampp/php/logs/php_errors.log');

header('Content-Type: application/json; charset=utf-8');
require_once 'User.php';
require_once 'Inventory.php';
session_start();

function checkAuth($required_role = null, $required_permission = null) {
    if (!isset($_SESSION['user_id'])) {
        http_response_code(401);
        echo json_encode(['success' => false, 'message' => 'Unauthorized']);
        exit;
    }
    if ($required_role && $_SESSION['role'] !== $required_role) {
        http_response_code(403);
        echo json_encode(['success' => false, 'message' => 'Forbidden: Incorrect role']);
        exit;
    }
    if ($required_permission && !in_array($required_permission, $_SESSION['permissions'])) {
        http_response_code(403);
        echo json_encode(['success' => false, 'message' => 'Forbidden: Insufficient permissions']);
        exit;
    }
}

$action = $_POST['action'] ?? $_GET['action'] ?? '';

switch ($action) {
    case 'check_session':
        if (isset($_SESSION['user_id'])) {
            echo json_encode(['success' => true, 'role' => $_SESSION['role'], 'full_name' => $_SESSION['full_name']]);
        } else {
            echo json_encode(['success' => false, 'message' => 'Not logged in']);
        }
        break;

    case 'login':
        if (!isset($_POST['email'], $_POST['password'], $_POST['role'])) {
            echo json_encode(['success' => false, 'message' => 'Missing required fields']);
            break;
        }
        $user = new User();
        $result = $user->login($_POST['email'], $_POST['password']);
        if ($result['success']) {
            $dashboards = [
                'inventory_manager' => 'dashboards/inventory-manager.html',
                'sales_manager' => 'dashboards/sales-manager.html',
                'system_admin' => 'dashboards/admin.html',
                'staff' => 'dashboards/staff.html'
            ];
            $result['redirect'] = $dashboards[$result['role']];
        }
        echo json_encode($result);
        break;

    case 'register':
        if (!isset($_POST['staff_id'], $_POST['full_name'], $_POST['email'], $_POST['phone'], $_POST['address'], $_POST['password'], $_POST['role'])) {
            echo json_encode(['success' => false, 'message' => 'Missing required fields']);
            break;
        }
        $user = new User();
        $permissions = isset($_POST['permissions']) ? json_decode($_POST['permissions'], true) : [];
        $result = $user->register(
            $_POST['staff_id'],
            $_POST['full_name'],
            $_POST['email'],
            $_POST['phone'],
            $_POST['address'],
            $_POST['password'],
            $_POST['role'],
            $permissions
        );
        echo json_encode($result);
        break;

    case 'reset_password':
        if (!isset($_POST['email'], $_POST['new_password'])) {
            echo json_encode(['success' => false, 'message' => 'Missing email or new password']);
            break;
        }
        $user = new User();
        $result = $user->resetPassword($_POST['email'], $_POST['new_password']);
        error_log("Password reset attempt for {$_POST['email']}: " . json_encode($result));
        echo json_encode($result);
        break;

    case 'logout':
        session_destroy();
        echo json_encode(['success' => true, 'redirect' => 'index.html']);
        break;

    case 'get_user':
        checkAuth('system_admin', 'manage_users');
        $user = new User();
        $result = $user->getUser($_GET['staff_id']);
        echo json_encode($result);
        break;

    case 'update_user':
        checkAuth('system_admin', 'manage_users');
        $user = new User();
        $permissions = isset($_POST['permissions']) ? json_decode($_POST['permissions'], true) : [];
        $result = $user->updateUser(
            $_POST['staff_id'],
            $_POST['full_name'],
            $_POST['email'],
            $_POST['phone'],
            $_POST['address'],
            $_POST['status'],
            $_POST['role'],
            $permissions
        );
        echo json_encode(['success' => $result, 'message' => $result ? 'User updated successfully' : 'Failed to update user']);
        break;

    case 'get_users':
        checkAuth('system_admin', 'manage_users');
        $user = new User();
        $result = $user->getAllUsers();
        echo json_encode($result);
        break;

    case 'add_item':
        checkAuth(null, 'manage_inventory');
        $inventory = new Inventory();
        $result = $inventory->addItem(
            $_POST['item_id'],
            $_POST['item_name'],
            $_POST['category'],
            $_POST['quantity'],
            $_POST['unit'],
            $_POST['price'],
            $_POST['supplier'],
            $_POST['reorder_level'],
            $_POST['description'],
            $_SESSION['user_id']
        );
        echo json_encode($result);
        break;

    case 'update_item':
        checkAuth(null, 'manage_inventory');
        $inventory = new Inventory();
        $result = $inventory->updateItem(
            $_POST['item_id'],
            $_POST['item_name'],
            $_POST['category'],
            $_POST['quantity'],
            $_POST['unit'],
            $_POST['price'],
            $_POST['supplier'],
            $_POST['reorder_level'],
            $_POST['description'],
            $_SESSION['user_id']
        );
        echo json_encode($result);
        break;

    case 'delete_item':
        checkAuth(null, 'manage_inventory');
        $inventory = new Inventory();
        $result = $inventory->deleteItem($_GET['item_id'], $_SESSION['user_id']);
        echo json_encode($result);
        break;

    case 'get_item':
        checkAuth();
        $inventory = new Inventory();
        $result = $inventory->getItem($_GET['item_id']);
        echo json_encode($result);
        break;

    case 'get_items':
        checkAuth();
        $inventory = new Inventory();
        $result = $inventory->getAllItems();
        echo json_encode($result);
        break;

    case 'get_updates':
        checkAuth();
        $inventory = new Inventory();
        $result = $inventory->getUpdates();
        echo json_encode($result);
        break;

    case 'get_stats':
        checkAuth();
        $inventory = new Inventory();
        $result = $inventory->getStats();
        echo json_encode($result);
        break;

    default:
        http_response_code(400);
        echo json_encode(['success' => false, 'message' => 'Invalid action']);
}

// Flush output buffer
ob_end_flush();
?>
