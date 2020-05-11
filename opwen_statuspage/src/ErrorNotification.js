import { notification } from 'antd';

function ErrorNotification({ message, exception }) {
  let description;

  if (exception.response && exception.response.data) {
    description =
      typeof exception.response.data === 'string'
        ? exception.response.data
        : exception.response.data.detail;
  } else {
    description = exception.message;
  }

  notification.error({ message, description });
}

export default ErrorNotification;
