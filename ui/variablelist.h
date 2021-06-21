#pragma once

#include <QtWidgets/QListView>
#include <QtWidgets/QWidget>

#include "dockhandler.h"
#include "uitypes.h"
#include "viewframe.h"

//! A variable list item can represent either a function-local variable, or a
//! data variable referenced by the current function.
enum class VariableListItemType {
    LocalVariable,
    DataVariable
};

//! An item part of VariableListModel.
class VariableListItem {
    FunctionRef m_func;
    VariableListItemType m_type;
    std::string m_name;

    uint64_t m_refPoint;

    BinaryNinja::Variable m_var;
    BinaryNinja::PossibleValueSet m_pvs;
    BinaryNinja::DataVariable m_dataVar;

public:
    //! Create a new VariableListItem of the LocalVariable type.
    VariableListItem(FunctionRef func, BinaryNinja::Variable var,
        BinaryNinja::PossibleValueSet pvs, std::string name);

    //! Create a new VariableListItem of the DataVariable type.
    VariableListItem(FunctionRef func, BinaryNinja::DataVariable dataVar,
        uint64_t refPoint, std::string name);

    //! Get the label representation of this item.
    QString label() const;

    uint64_t refPoint() const;
};

//! The backing model for the variable list widget, holds VariableListItem.
class BINARYNINJAUIAPI VariableListModel : public QAbstractListModel {
    Q_OBJECT

    ViewFrame* m_view;
    BinaryViewRef m_data;
    FunctionRef m_func;
    std::vector<VariableListItem> m_vars;

public:
    VariableListModel(QWidget* parent, ViewFrame* view, BinaryViewRef data);

    //! Set the focused function and update the content of the list.
    void setFunction(FunctionRef func, BNFunctionGraphType il);

    // -- QAbstractListModel --

    virtual QVariant data(const QModelIndex& i, int role) const override;
    virtual QModelIndex index(int row, int col,
        const QModelIndex& parent = QModelIndex()) const override;

    virtual int columnCount(const QModelIndex& parent = QModelIndex()) const override;
    virtual int rowCount(const QModelIndex& parent = QModelIndex()) const override;

    Qt::ItemFlags flags(const QModelIndex& index) const override;
    virtual QVariant headerData(int column, Qt::Orientation orientation,
        int role) const override;
};

//! The main variable list dock widget.
class BINARYNINJAUIAPI VariableListView : public QWidget, public DockContextHandler {
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
