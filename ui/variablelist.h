#pragma once

#include <QtWidgets/QListView>
#include <QtWidgets/QWidget>

#include "dockhandler.h"
#include "uitypes.h"
#include "viewframe.h"

enum class VariableListItemType {
    LocalVariable,
    DataVariable
};

class VariableListItem {
    FunctionRef m_func;
    VariableListItemType m_type;
    std::string m_name;

    BinaryNinja::Variable m_var;
    BinaryNinja::DataVariable m_dataVar;
    BinaryNinja::VariableNameAndType m_nat;

public:
    VariableListItem(FunctionRef func, BinaryNinja::Variable var,
        BinaryNinja::VariableNameAndType nat);
    VariableListItem(FunctionRef func, BinaryNinja::DataVariable dataVar,
        std::string name);

    QString label() const;
};

using VariableList = std::vector<VariableListItem>;

class BINARYNINJAUIAPI VariableListModel : public QAbstractListModel {
    Q_OBJECT

    ViewFrame* m_view;
    BinaryViewRef m_data;
    FunctionRef m_func;
    VariableList m_vars;

public:
    VariableListModel(QWidget* parent, ViewFrame* view, BinaryViewRef data);

    void setFunction(FunctionRef func);

    virtual QVariant data(const QModelIndex& i, int role) const override;
    virtual QModelIndex index(int row, int col,
        const QModelIndex& parent = QModelIndex()) const override;

    virtual int columnCount(const QModelIndex& parent = QModelIndex()) const override;
    virtual int rowCount(const QModelIndex& parent = QModelIndex()) const override;

    Qt::ItemFlags flags(const QModelIndex& index) const override;
    virtual QVariant headerData(int column, Qt::Orientation orientation,
        int role) const override;
};

class BINARYNINJAUIAPI VariableListView
    : public QWidget,
      public DockContextHandler {
    Q_OBJECT
    Q_INTERFACES(DockContextHandler)

    ViewFrame* m_view;
    BinaryViewRef m_data;

    VariableListModel* m_listModel;
    QListView* m_list;

public:
    VariableListView(ViewFrame* view, BinaryViewRef data);

    void updateContent();
};
