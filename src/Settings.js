import React from 'react';
import { Button, Form, Icon, Input, InputNumber } from 'antd';
import axios from 'axios';

const githubApi = axios.create({ baseURL: 'https://api.github.com' });

const formatSeconds = value => `${value} seconds`;
const parseSeconds = value => value.replace(/[^0-9]/g, '');

const colors = {
  icon: 'rgba(0, 0, 0, .25)',
};

class SettingsForm extends React.Component {
  _validateGithubAccessToken = async (_rule, value, callback) => {
    const { form } = this.props;

    if (!value) {
      form.setFieldsValue(
        {
          githubUsername: undefined,
          githubAvatarUrl: undefined,
        },
        callback
      );
      return;
    }

    let response;
    try {
      response = await githubApi.get('/user', {
        headers: { Authorization: `Token ${value}` },
      });
    } catch (error) {
      callback(error.response.data.message);
      return;
    }

    form.setFieldsValue(
      {
        githubUsername: response.data.login,
        githubAvatarUrl: response.data.avatar_url,
      },
      callback
    );
  };

  handleSubmit = e => {
    const { form, onChange } = this.props;

    e.preventDefault();

    form.validateFields((err, values) => {
      if (!err) {
        onChange({ ...values, updatedAt: `${new Date()}` });
      }
    });
  };

  render() {
    const { form } = this.props;

    const {
      serverEndpoint,
      githubAccessToken,
      githubUsername,
      githubAvatarUrl,
      pingIntervalSeconds,
    } = this.props.initialValue;

    return (
      <Form onSubmit={this.handleSubmit}>
        <Form.Item label="Server endpoint">
          {form.getFieldDecorator('serverEndpoint', {
            rules: [
              {
                required: true,
                message: 'Please input the endpoint URL of the Lokole server',
              },
            ],
            initialValue: serverEndpoint,
          })(
            <Input
              prefix={<Icon type="api" style={{ color: colors.icon }} />}
              placeholder="http://localhost:8080"
            />
          )}
        </Form.Item>
        <Form.Item label="Github access token">
          {form.getFieldDecorator('githubAccessToken', {
            rules: [{ validator: this._validateGithubAccessToken }],
            initialValue: githubAccessToken,
          })(
            <Input.Password
              prefix={<Icon type="github" style={{ color: colors.icon }} />}
              placeholder="1234567abcdefgh"
            />
          )}
        </Form.Item>
        <Form.Item style={{ display: 'none' }}>
          {form.getFieldDecorator('githubUsername', {
            initialValue: githubUsername,
          })(<Input readOnly hidden />)}
        </Form.Item>
        <Form.Item style={{ display: 'none' }}>
          {form.getFieldDecorator('githubAvatarUrl', {
            initialValue: githubAvatarUrl,
          })(<Input readOnly hidden />)}
        </Form.Item>
        <Form.Item label="Ping interval">
          {form.getFieldDecorator('pingIntervalSeconds', {
            rules: [
              {
                required: true,
                message: 'Please input the ping interval in seconds',
              },
            ],
            initialValue: pingIntervalSeconds,
          })(
            <InputNumber
              style={{ width: '100%' }}
              placeholder="10 seconds"
              formatter={formatSeconds}
              parser={parseSeconds}
              min={1}
              max={60}
            />
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
