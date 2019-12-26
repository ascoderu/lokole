import React from 'react';
import { Button, Form, Icon, Input, InputNumber } from 'antd';
import axios from 'axios';

const githubApi = axios.create({ baseURL: 'https://api.github.com' });

const formatSeconds = value => `${value} seconds`;
const parseSeconds = value => value.replace(/[^0-9]/g, '');

const formatMillis = value => `${value} ms`;
const parseMillis = value => value.replace(/[^0-9]/g, '');

const colors = {
  icon: 'rgba(0, 0, 0, .25)',
};

class SettingsForm extends React.Component {
  _validateGithubAccessToken = async (_rule, value, callback) => {
    const { setFieldsValue } = this.props.form;

    if (!value) {
      setFieldsValue({
        githubUsername: undefined,
        githubAvatarUrl: undefined,
      }, callback);
      return;
    }

    try {
      const response = await githubApi.get('/user', {
        headers: { Authorization: `Token ${value}` }
      })
      setFieldsValue({
        githubUsername: response.data.login,
        githubAvatarUrl: response.data.avatar_url,
      }, callback);
    } catch (error) {
      callback(error.response.data.message);
      return;
    }
  };

  handleSubmit = e => {
    e.preventDefault();

    this.props.form.validateFields((err, values) => {
      if (!err) {
        this.props.onChange({ ...values, updatedAt: `${new Date()}` });
      }
    });
  };

  render() {
    const { getFieldDecorator } = this.props.form;

    return (
      <Form onSubmit={this.handleSubmit}>
        <Form.Item label="Server endpoint">
          {getFieldDecorator('serverEndpoint', {
            rules: [{ required: true, message: 'Please input the server endpoint!' }],
            initialValue: this.props.initialValue.serverEndpoint,
          })(
            <Input
              prefix={<Icon type="api" style={{ color: colors.icon }} />}
              placeholder="http://localhost:8080"
            />,
          )}
        </Form.Item>
        <Form.Item label="Github access token">
          {getFieldDecorator('githubAccessToken', {
            rules: [{ validator: this._validateGithubAccessToken }],
            initialValue: this.props.initialValue.githubAccessToken,
          })(
            <Input.Password
              prefix={<Icon type="github" style={{ color: colors.icon }} />}
              placeholder="1234567abcdefgh"
            />,
          )}
        </Form.Item>
        <Form.Item style={{display: 'none' }}>
          {getFieldDecorator('githubUsername', {
            initialValue: this.props.initialValue.githubUsername,
          })(
            <Input readOnly hidden />,
          )}
        </Form.Item>
        <Form.Item style={{display: 'none' }}>
          {getFieldDecorator('githubAvatarUrl', {
            initialValue: this.props.initialValue.githubAvatarUrl,
          })(
            <Input readOnly hidden />,
          )}
        </Form.Item>
        <Form.Item label="Ping interval">
          {getFieldDecorator('pingIntervalSeconds', {
            rules: [{ required: true, message: 'Please input the ping interval in seconds' }],
            initialValue: this.props.initialValue.pingIntervalSeconds,
          })(
            <InputNumber
              style={{ width: '100%' }}
              prefix={<Icon type="clock-circle" style={{ color: colors.icon }} />}
              placeholder="10 seconds"
              formatter={formatSeconds}
              parser={parseSeconds}
              min={1}
              max={60}
            />,
          )}
        </Form.Item>
        <Form.Item label="Ping maximum latency">
          {getFieldDecorator('pingMaxLatencyMillis', {
            rules: [{ required: true, message: 'Please input the maximum acceptable ping latency in milliseconds' }],
            initialValue: this.props.initialValue.pingMaxLatencyMillis,
          })(
            <InputNumber
              style={{ width: '100%' }}
              prefix={<Icon type="clock-circle" style={{ color: colors.icon }} />}
              placeholder="100 ms"
              formatter={formatMillis}
              parser={parseMillis}
              min={50}
              max={2000}
            />,
          )}
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">
            Save settings
          </Button>
        </Form.Item>
      </Form>
    );
  }
}

export default Form.create({ name: 'settings' })(SettingsForm);
