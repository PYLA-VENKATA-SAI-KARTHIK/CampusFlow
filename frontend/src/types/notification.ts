export interface NotificationItem {
  id: string;
  user_id: string;
  title: string;
  body: string;
  notification_type: string;
  reference_id: string | null;
  reference_type: string | null;
  is_read: boolean;
  push_sent: boolean;
  push_sent_at: string | null;
  created_at: string;
}

export interface PaginatedNotifications {
  items: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export type BroadcastAudience = 'ELIGIBLE' | 'REGISTERED' | 'SHORTLISTED';

export interface ManualBroadcastRequest {
  audience: BroadcastAudience;
  title: string;
  body: string;
}

export interface ManualBroadcastResponse {
  message: string;
  recipient_count: number;
}
